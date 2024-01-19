# To start kafka now and restart at login:  brew services start kafka
# Or, if you don't want/need a background service you can just run:
# /opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties
from bcc import BPF
from kafka import KafkaProducer
from ctypes import cast, Structure, POINTER, c_uint, c_ushort, c_ulonglong

import signal

# Function to handle SIGINT (Ctrl-C)
def sigint_handler(signal, frame):
    global exit_flag
    print("\nSIGINT received! Exit")
    producer.close()
    bpf.detach_kprobe(event="tcp_sendmsg")
    bpf.detach_kprobe(event="tcp_recvmsg")
    exit(1)



# Set the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)

# Specify Kafka servers and api
kafka_bootstrap_servers = 'kafka-container:9092'
desired_api_version = (0, 11, 5)
# Specify Kafka topic and key
kafka_topic = "tcp_ebpf_event"
kafka_key = None  # Add a key if needed


# Initialize Kafka producer
try:
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        api_version=desired_api_version,
        value_serializer=lambda v: str(v).encode('utf-8')
    )
except Exception as e:
    print(f"Failed to connect to Kafka: {e}")
    exit(1)

class EventData(Structure):
    _fields_ = [("src_ip", c_uint),
                ("dest_ip", c_uint),
                ("src_port", c_ushort),
                ("dest_port", c_ushort),
                ("pid", c_uint),
                ("func_id", c_ushort),
                ("timestamp", c_ulonglong)]

def handle_event(cpu, event_data, size):

    e_data = cast(event_data, POINTER(EventData)).contents

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

    # Process data (e.g., send to Kafka)
    producer.send(kafka_topic, key=kafka_key, value=event_json)


# Load BPF program
bpf = BPF(src_file="tcp_events.c")

bpf.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")
bpf.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")

bpf.trace_print()

# Open perf "events" buffer, loop with callback to handle_event
bpf["events"].open_perf_buffer(handle_event)

# Process data

try:
    while True:
        # Retrieve data from eBPF map
        bpf.perf_buffer_poll()

except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")

finally:
    #Cleanup code here (if needed)
    # Close Kafka producer and detach probe
    print("Close Kafka producer and detach probes")
    producer.close()
    bpf.detach_kprobe(event="tcp_sendmsg")
    bpf.detach_kprobe(event="tcp_recvmsg")
    pass

