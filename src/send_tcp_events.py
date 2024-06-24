# To start kafka now and restart at login:  brew services start kafka
# Or, if you don't want/need a background service you can just run:
# /opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties
import sys
print(sys.path)
from bcc import BPF
from kafka import KafkaProducer
from ctypes import cast, Structure, POINTER, c_uint, c_ushort, c_ulonglong, c_char
import json
import signal
from kafka import __version__ as kafka_python_version
import os
import configparser
import psutil
import socket
import docker
import struct

#
# Read Configuration file
#
def read_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)

    kafka_config = {
        'enabled': os.getenv('KAFKA_STREAMING_ENABLED', config.getboolean('kafka_events_server', 'enabled', fallback=True)),
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', config.get('kafka_events_server', 'bootstrap_servers')),
        'group_id' : os.getenv('KAFKA_GROUP_ID', config.get('kafka_events_server', 'group_id')),
        'topic': os.getenv('KAFKA_TOPIC', config.get('kafka_events_server', 'topic')),
        'acks': os.getenv('KAFKA_ACKS', config.get('kafka_events_server', 'acks')),
        'api_version': tuple(map(int, os.getenv('KAFKA_API_VERSION', config.get('kafka_events_server', 'api_version')).split(','))),
        # Add more Kafka settings as needed
    }
    
    # Get the process_names from the tcp_event section in the config file
    process_names_str = config.get('tcp_events', 'process_names', fallback='')

    # Override with environment variable if provided
    process_names_env = os.getenv('PROCESS_NAMES_OVERRIDE', '')
    if process_names_env:
        process_names_str = process_names_env

    # Convert the comma-separated string to a list, removing any empty strings
    process_names = [name.strip() for name in process_names_str.split(',') if name.strip()]

    # Set a boolean based on whether the list is empty or not
    process_names_empty = all(name == "''" for name in process_names)

    # Print the boolean value and the final list of process_names
    print(f'Is process_names empty? {process_names_empty}')
    print(f'Final process_names: {process_names}')

    # Create the tcp_event_config dictionary
    hostname =os.getenv('HOSTNAME') or "producer-mtk"
        
    tcp_event_config = {
        'container': os.getenv('MTK_CONTAINER', config.get('tcp_events', 'container_name', fallback=hostname)),
        'http_only': os.getenv('HTTP_EVENTS_ONLY', config.getboolean('tcp_events', 'http_only', fallback=False)),
        'comm_filtering': not process_names_empty,
        'process_names': process_names,
        'enabled': os.getenv('EVENTS_STREAMING', config.getboolean('tcp_events', 'streaming', fallback=True)),
        # Add more TCP event settings as needed
    }    
 
    if tcp_event_config.get('comm_filtering') is True :
        print(f"Comm Filter: {tcp_event_config.get('comm_filtering')} on Names: {tcp_event_config.get('process_names')}, Data Stream: {tcp_event_config.get('enabled')}")
    if tcp_event_config.get('http_only') is True :
        print("HTTP sending ONLY")

    return kafka_config, tcp_event_config

#
#  Setup Kafka producer for data transmission
#
def create_kafka_producer(kaf_config):
    producer_config = {
        'bootstrap_servers': kaf_config['bootstrap_servers'],
        'acks': kaf_config['acks'],
        'api_version': kaf_config['api_version'],
        # Add more Kafka producer settings as needed
    }

    producer = KafkaProducer(**producer_config)
    return producer

def get_container(pid):
    container_name = tcp_event_config.get('container')
        
    container_id = 0
    with open('/proc/self/cgroup', 'r') as f:
        for line in f:
            if 'docker' in line:
                # Extract the container ID from the cgroup entry
                container_id = line.split('/')[-1].strip()
                break

    if container_id:
        with open(f'/proc/{container_id}/cgroup', 'r') as f:
            for line in f:
                if 'docker' in line:
                    # Extract the container name from the cgroup entry
                    container_name = line.split('/')[-1].strip()
                    return container_name

    return container_name

    
def get_dns_name(dest_ip):
    # Convert dest_ip to a bytes-like object
    dest_ip_bytes = struct.pack('!I', dest_ip)
    
    try:
        # Use socket library for DNS resolution
        host_name, _, _ = socket.gethostbyaddr(socket.inet_ntoa(dest_ip_bytes))       
        return host_name

    except socket.herror as e:
        # Handle DNS resolution errors
        d_name = f"{socket.inet_ntoa(struct.pack('!I', dest_ip))}" 
        print(f"Error get dns name for {dest_ip}: {e}. Using {d_name} instead")
        return d_name
    
def get_local_process_name(pid):
    try:
        # Use the psutil library to query process information
        process = psutil.Process(pid)
        process_name = process.name()
        return process_name
        #return None
    except psutil.NoSuchProcess:
        # Handle the case where the process with the given PID does not exist
        print(f"Error getting local process name for {pid}: {psutil.NoSuchProcess}")
        return None



#
# Create Signal Interrupt handling- SIGINT (Ctrl-C) to end collection
#
def sigint_handler(signal, frame):
    global exit_flag
    exit_flag = True
    print("\nSIGINT received! Exit")
    exit(1)


#
# Begin Program Execution
#
        
# Start the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)

#
# Get settings for Kafka, TCP event handling, and reporting from the config file
kafka_config, tcp_event_config = read_config()


# Check environment variable determine if console output is desired 
# instead of kafka for data transmission 
if tcp_event_config['enabled'] is False:
    print("Print to console.  Data streaming is off")
    #bpf.trace_print() # bpf.trace_print prevents bpf event poll handler from executing.
   
# Initialize Kafka producer
try:
    # Create Kafka producer
    producer = create_kafka_producer(kafka_config)
    # Producer success message
    print(f"Kafka producer connected (Kafka python version {kafka_python_version} at {producer.config['bootstrap_servers']})")

except Exception as e:
    print(f"Failed to create Kafka Producer: ({kafka_python_version}) {e}")
    exit(1)

# 
# BPF tcp event extraction, data transformation and loading into userspace 

print("open file")
# Read the content of the BPF program file
with open('bpf_tcp_events.c', 'r') as f:
    bpf_program_code = f.read()
print("load bpf")
# Load BPF program
bpf = BPF(text=bpf_program_code)

print("Attaching to kprobes")
# Attach bpf events to kprobe
bpf.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")
bpf.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")
print("Attached to kprobes")

#
#   Data Producing / BPF Event handling
#
TASK_COMM_LEN = 17  # Assuming the TASK_COMM_LEN value
TASK_PAYLOAD_SIZE = 150

class EventData(Structure):
    _fields_ = [
        ('event_id', c_ushort),
        ('src_ip', c_uint),
        ('dest_ip', c_uint),
        ('src_port', c_ushort),
        ('dest_port', c_ushort),
        ('pid', c_uint),
        ('tid', c_uint),
        ('timeoffset_ns', c_ulonglong),
        ('flags', c_ushort),          # Flags field in the TCP header (URG, ACK, PSH, RST, SYN, FIN)  
        ('seq', c_uint),        # Sequence number in the TCP header
        ('ack', c_uint),        # Acknowledgment number in the TCP header
        ('window', c_ushort),    # Window size in the TCP header
        ('payload_size', c_uint),
        ('payload', c_char * TASK_PAYLOAD_SIZE),  # Adjust the size based on your payload size
    ]

# Map for associating PID with metadata
pid_metadata_map = {}
pid_to_ppid_map = {}
dns_metadata_map = {}


# Kafka output from bpf event probes
def handle_event(cpu, event_data, size):
    global exit_flag
    if exit_flag==True:
        return

    # Process bpf collector event from userspace 
    eventData = cast(event_data, POINTER(EventData)).contents

    # Analyze HTTP header
    # Example: Check for the presence of "HTTP/1." to identify an HTTP packet
    status_code = -1
    content_type = 'unknown'
    content_length = eventData.payload_size

    # check for zero content length before decoding the paylaod
    if content_length>0 and content_length<=1500 : # only read data if it seems reasonable
        try: 
            print(f"valid content length range {content_length}!")
            http_response = eventData.payload.decode('utf-8')
            # Search for status code
            print("search for status code start!")
            status_code_start = http_response.find('HTTP/1.') + len('HTTP/1.')
            if status_code_start>6: #status code was not -1
                print("HTTP DATA!")
            
                print(f"extract status at start {status_code_start}")
                status_code_end = http_response.find(' ', status_code_start)
                print(f"status code end {status_code_end}")
                status_code_start = status_code_end+1
                print(f"status code start2 {status_code_start}")
                status_code_end = http_response.find(' ', status_code_start)
                print(f"status code end2 {status_code_end}")
                status_code = int(http_response[status_code_start:status_code_end])

                # Search for content type
                print("search for content type")
                content_type_start = http_response.find('Content-Type: ') + len('Content-Type: ')
                content_type_end = http_response.find('\r\n', content_type_start)
                content_type = http_response[content_type_start:content_type_end]

                # Search for content length
                print("search for content length")
                content_length_start = http_response.find('Content-Length: ') + len('Content-Length: ')
                content_length_end = http_response.find('\r\n', content_length_start)
                content_length = int(http_response[content_length_start:content_length_end])
                print("processed http message")

        except UnicodeDecodeError as err:
            # Handle the case when payload is not valid UTF-8 text
            print(f"Error on Unicode decode {err=}, {type(err)=}")
            content_type = "application/octet-stream"
        except Exception as e:
            print(f"Unexpected content {e=}, {type(e)=}")    
            content_type = "application/octet-stream"

    #
    #   get names from pid 
    #
            
    #   get comm name        
    try:
        # Use the psutil library to query process (pid) information
        
        # get pid comm name
        if eventData.pid not in pid_metadata_map:
            # map eventData.pid comm name
            pid_comm = get_local_process_name(eventData.pid)
            pid_metadata_map[eventData.pid] = pid_comm
            #pid_metadata_map[ppid] = ppid_comm
        else :    
            # get pid comm name
            pid_comm = pid_metadata_map[eventData.pid]   

        # get ppid
        if eventData.pid not in pid_to_ppid_map:
            # map pid to ppid
            process = psutil.Process(eventData.pid)
            ppid = process.ppid()
            pid_to_ppid_map[eventData.pid] = ppid
        else :
            ppid = pid_to_ppid_map[eventData.pid]  

        # get ppid comm name
        if  ppid not in pid_metadata_map :    
            # map the ppid comm name
            ppid_comm = get_local_process_name(ppid)
            pid_metadata_map[ppid] = ppid_comm
        else :
            ppid_comm = pid_metadata_map[ppid]   

        # get tid comm name
        if  eventData.tid not in pid_metadata_map :    
            # map the ppid comm name
            tid_process = psutil.Process(eventData.tid)
            tid_comm = tid_process.name()
            pid_metadata_map[eventData.tid] = tid_comm
        else :
            tid_comm = pid_metadata_map[eventData.tid]          

    except psutil.NoSuchProcess:      
        print(f"Error getting process name for pid {eventData.pid}:{pid_comm} or ppid: {ppid}:{ppid_comm} {psutil.NoSuchProcess}")
     
    # get container name from pid     
                      
    # find a dns name for the dest ip, if any
    if eventData.dest_ip not in pid_metadata_map:
        d_name = get_dns_name(eventData.dest_ip)
        pid_metadata_map[eventData.dest_ip] = d_name
    else:
        d_name = pid_metadata_map[eventData.dest_ip]    

    container = get_container(eventData.pid)

    print(f"Send p_comm:{pid_comm}, pp_comm: {ppid_comm}, tid_comm: {tid_comm}, cntnr:{container},  dst_dns:{d_name}, pid: {eventData.pid}, ppid: {ppid}, tid:{eventData.tid}, content_len:{content_length}  flags:{eventData.flags} content_type {content_type} status_code {status_code}  eventid {eventData.event_id}")
    
    # Serialize the entire eventData structure to python dictionary 
    event_json = {
        'event_id': eventData.event_id,
        'src_ip': eventData.src_ip,
        'dest_ip': eventData.dest_ip,
        'src_port': eventData.src_port,
        'dest_port': eventData.dest_port,
        'pid': eventData.pid,
        'tid': eventData.tid,
        'flags': eventData.flags,
        'window': eventData.window,
        'timeoffset_ns': eventData.timeoffset_ns,
        'ppid': ppid,
        'comm' : pid_comm,
        'pcomm': ppid_comm,
        'tcomm': tid_comm,
        'container' : container,
        'dest_name' : d_name, 
        # Add other fields as needed
        'status_code': status_code,
        'content_type': content_type,
        'content_length': content_length
    }
    
    # see if event comm name is in list of process_name to filter for
    if tcp_event_config['comm_filtering'] and event_json.get('comm') not in tcp_event_config['process_names']:
        print(f"{event_json.get('comm')} not found in {tcp_event_config['process_names']}") # Produce a trace message
        return
    
    # Serialize the event dictionary to a JSON string
    json_data = json.dumps(event_json)
    
    # Process data (e.g., send to Kafka broker / topic)
    try:
        producer.send(kafka_config['topic'], value=json_data.encode('utf-8')).get(timeout=2)
        # Block for 'timeout' seconds and raises an exception if the record is not sent successfully
        # print(f"Message sent to topic {record_metadata.topic} at partition {record_metadata.partition}, offset {record_metadata.offset}")
    
    except Exception as err:
        print(f"Error on kafka producer send {err=}, {type(err)=}")
        exit_flag = True


# Open bpf perf "events" buffer for and attach callback to handle probed-for events
events = bpf["events"]
events.open_perf_buffer(handle_event)
print("Connected to bpf events")

# Process data
exit_flag = False

try:
    while not exit_flag:
        # Retrieve data from eBPF map
        print("Poll for event data")
        bpf.perf_buffer_poll()
        if exit_flag:
            break

except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")

finally:
    # Cleanup code here (if needed)
    # Close Kafka producer and detach probe
    print("Close Kafka producer and detach probes")
    producer.close()
    bpf.detach_kprobe(event="tcp_sendmsg")
    bpf.detach_kprobe(event="tcp_recvmsg")
    pass

