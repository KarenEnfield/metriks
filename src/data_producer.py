# To start kafka now and restart at login:  brew services start kafka
# Or, if you don't want/need a background service you can just run:
# /opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties
from bcc import BPF
from kafka import KafkaProducer
from ctypes import cast, Structure, POINTER, c_uint, c_ushort, c_ulonglong, c_char
import json
import signal
from kafka import __version__ as kafka_python_version
import os
import configparser

#
# Read Configuration file
#
def read_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)

    kafka_config = {
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', config.get('kafka', 'bootstrap_servers')),
        'group_id' : os.getenv('KAFKA_GROUP_ID', config.get('kafka', 'group_id')),
        'topic': os.getenv('KAFKA_TOPIC', config.get('kafka', 'topic')),
        'acks': os.getenv('KAFKA_ACKS', config.get('kafka', 'acks')),
        'api_version': tuple(map(int, os.getenv('KAFKA_API_VERSION', config.get('kafka', 'api_version')).split(','))),
        # Add more Kafka settings as needed
    }
    
    # Get the process_names from the tcp_event section in the config file
    process_names_str = config.get('tcp_event', 'process_names', fallback='')

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
    tcp_event_config = {
        'comm_filtering': not process_names_empty,
        'process_names': process_names,
        # Add more TCP event settings as needed
    }    

    # Read the 'enabled' value from the INI file and use the default of True
    data_streaming_config = {
        'enabled': os.getenv('DATA_STREAMING_ENABLED', config.getboolean('data_streaming', 'enabled', fallback=True)),
        # Add more data_streaming settings as needed
    }
    
    if tcp_event_config.get('comm_filtering') is True :
        print(f"Comm Filter: {tcp_event_config.get('comm_filtering')} on Names: {tcp_event_config.get('process_names')}, Data Stream: {data_streaming_config.get('enabled')}")

    return kafka_config, tcp_event_config, data_streaming_config#

#
#  Setup Kafka producer for data transmission
#
def create_kafka_producer(kafka_config):
    producer_config = {
        'bootstrap_servers': kafka_config['bootstrap_servers'],
        'acks': kafka_config['acks'],
        'api_version': kafka_config['api_version'],
        # Add more Kafka producer settings as needed
    }

    producer = KafkaProducer(**producer_config)
    return producer

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
kafka_config, tcp_event_config, data_streaming_config = read_config()

# 
# BPF tcp event extraction, data transformation and loading into userspace 
bpf_collector_c = 'bpf_collector.c'

# Load BPF program
bpf = BPF(src_file=bpf_collector_c)
events = bpf["events"]

# Attach to bpf events to probe
# TBA Probe filtering ...
bpf.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")
bpf.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")


# Check environment variable determine if console output is desired 
# instead of kafka for data transmission 
if data_streaming_config['enabled'] is False:
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
#   Data Producing / BPF Event handling
#
TASK_COMM_LEN = 16  # Assuming the TASK_COMM_LEN value

class EventData(Structure):
    _fields_ = [
        ('src_ip', c_uint),
        ('dest_ip', c_uint),
        ('src_port', c_ushort),
        ('dest_port', c_ushort),
        ('pid', c_uint),
        ('func_id', c_ushort),
        ('timeoffset_ns', c_ulonglong),
        ('comm', c_char * TASK_COMM_LEN)  # Add the 'comm' field
    ]

# Kafka output from bpf event probes
def handle_event(cpu, event_data, size):
    global exit_flag
    if exit_flag==True:
        return

    # Process bpf collector event from userspace 
    eventData = cast(event_data, POINTER(EventData)).contents

    # TBA Process name filtering ...
    # Serialize the entire event structure to JSON (for example)
    event_json = {
        'src_ip': eventData.src_ip,
        'dest_ip': eventData.dest_ip,
        'src_port': eventData.src_port,
        'dest_port': eventData.dest_port,
        'pid': eventData.pid,
        'func_id': eventData.func_id,
        'timeoffset_ns': eventData.timeoffset_ns,
        'comm' : eventData.comm.decode('utf-8'),
        # Add other fields as needed
    }

    # see if event comm name is in list of process_name to filter for
    if tcp_event_config['comm_filtering'] and event_json.get('comm') not in tcp_event_config['process_names']:
        print(f"{event_json.get('comm')} not found in {tcp_event_config['process_names']}") # Produce a trace message
        return

    # Convert the dictionary to a JSON string
    json_data = json.dumps(event_json)
    
    # Process data (e.g., send to Kafka broker / topic)
    try:
        producer.send(kafka_config.get('topic'), value=json_data.encode('utf-8')).get(timeout=3)
  
        # Block for 'timeout' seconds and raises an exception if the record is not sent successfully
        # print(f"Message sent to topic {record_metadata.topic} at partition {record_metadata.partition}, offset {record_metadata.offset}")
    
    except Exception as err:
        print(f"Error on kafka producer send {err=}, {type(err)=}")
        exit_flag = True

# Open bpf perf "events" buffer for and attach callback to handle probed-for events
bpf["events"].open_perf_buffer(handle_event)
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

