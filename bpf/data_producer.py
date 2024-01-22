# To start kafka now and restart at login:  brew services start kafka
# Or, if you don't want/need a background service you can just run:
# /opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties
from bcc import BPF
from kafka import KafkaProducer
from ctypes import cast, Structure, POINTER, c_uint, c_ushort, c_ulonglong
import json
import signal
from kafka import __version__ as kafka_python_version
import os
import configparser

#
# Configuration setup
#
producer_settings_ini = 'producer_settings.ini'
config_file = configparser.ConfigParser()
config_file.read(producer_settings_ini)

# Defining this environment variable will override for console mode, no kafka
env_console_no_kafka = "CONSOLE_NO_KAFKA"
# Retrieve values from 'Settings' section
settings = {}
if env_console_no_kafka in os.environ: # env variable exists, override defaults; defaults to False
    env_value_str = os.environ.get(env_console_no_kafka, 'False')
    env_value_bool = env_value_str.lower() == 'true'
    settings['console_no_kafka'] = env_value_bool
elif 'Settings' in config_file:
    settings['console_no_kafka'] = config_file['Settings'].getboolean('console_no_kafka', fallback=False)
else:
    settings['console_no_kafka'] = False

# Retrieve process names and probe names from 'EventFilters' section
# 
process_names = []
probe_names = []

if 'EventFilters' in config_file:
    process_names = [value.strip() for value in config_file['EventFilters'].get('process_names', '').split('\n') if value.strip()]
    probe_names = [value.strip() for value in config_file['EventFilters'].get('probe_names', '').split('\n') if value.strip()]



# Signal Interrupt handling- SIGINT (Ctrl-C)
def sigint_handler(signal, frame):
    global exit_flag
    exit_flag = True
    print("\nSIGINT received! Exit")
    exit(1)

# Set the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)

# 
# BPF Probe setup
# 
bpf_collector_c = 'bpf_collector.c'

# Load BPF program
bpf = BPF(src_file=bpf_collector_c)
events = bpf["events"]

# Attach to bpf events to probe
# TBA Probe filtering ...
bpf.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")
bpf.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")

# Check environment variable determine if console output is desired 
# instead of kafka sends for 
# bpf event reporting. 
# bpf.trace_print prevents bpf event poll handler from executing.
if settings['console_no_kafka'] is True:
    bpf.trace_print()


#
# Kafka Communication Setup
#
    
# Define Kafka server, api, and data topic for probe data sends
kafka_bootstrap_servers = 'kafka-container:9092'
desired_api_version = (0, 11)
kafka_topic = 'tcp-events'

# Initialize Kafka producer
try:
    producer = KafkaProducer(
        bootstrap_servers=[kafka_bootstrap_servers],
        api_version=desired_api_version
    )
    
    print(f"Kafka producer connected (Kafka python version {kafka_python_version} at {producer.config['bootstrap_servers']})")

except Exception as e:
    print(f"Failed to connect to Kafka ({kafka_python_version}) {e}")
    exit(1)

#
#   Data Producing / BPF Event handling
#
class EventData(Structure):
    _fields_ = [('src_ip', c_uint),
                ('dest_ip', c_uint),
                ('src_port', c_ushort),
                ('dest_port', c_ushort),
                ('pid', c_uint),
                ('func_id', c_ushort),
                ('timestamp', c_ulonglong)]


# Kafka output from bpf event probes
def handle_event(cpu, event_data, size):
    global exit_flag
    if exit_flag==True:
        return
    
    # Process bpf collector event from userspace 
    e_data = cast(event_data, POINTER(EventData)).contents
    
    # TBA Process name filtering ...
    # Serialize the entire event structure to JSON (for example)
    event_json = {
        'src_ip': e_data.src_ip,
        'dest_ip': e_data.dest_ip,
        'src_port': e_data.src_port,
        'dest_port': e_data.dest_port,
        'pid': e_data.pid,
        'func_id': e_data.func_id,
        'timestamp': e_data.timestamp,
        # Add other fields as needed
    }
    
    # Convert the dictionary to a JSON string
    json_data = json.dumps(event_json)
    
    # Process data (e.g., send to Kafka broker / topic)
    try:
        record_metadata = producer.send(kafka_topic, value=json_data.encode('utf-8')).get(timeout=3)
  
        # Block for 'timeout' seconds and raises an exception if the record is not sent successfully
        print(f"Message sent to topic {record_metadata.topic} at partition {record_metadata.partition}, offset {record_metadata.offset}")
    
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

