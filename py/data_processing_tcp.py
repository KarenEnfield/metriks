from bcc import BPF
from kafka import KafkaProducer

# Initialize Kafka producer
producer = KafkaProducer(bootstrap_servers='kafka-server:9092')

# Attach eBPF program
bpf = BPF(src_file="tcp_trace.c")
bpf.attach_tracepoint(tp="tcp:tcp_v{4,6}_connect", fn_name="trace_tcp_connect")

# Process data
while True:
    try:
        # Retrieve data from eBPF map
        ipv4_key = bpf["events"].event()
        
        # Process data (e.g., send to Kafka)
        producer.send('tcp_connections_topic', str(ipv4_key))

    except KeyboardInterrupt:
        break
