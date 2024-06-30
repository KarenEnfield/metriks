from bcc import BPF
from kafka import KafkaProducer
import json

# Kafka broker configuration
kafka_broker = 'localhost:9092'

# Initialize Kafka producer
producer_config = {
    'bootstrap_servers': kafka_broker,
    'acks': 'all',
    'api_version': '0,11',
    # Add more Kafka producer settings as needed
}
producer = KafkaProducer(**producer_config)

# Kafka topic names
http_topic = 'http_metrics'
tcp_topic = 'tcp_metrics'
udp_topic = 'udp_metrics'
dns_topic = 'dns_metrics'

# Initialize eBPF programs
bpf_http = BPF(src_file='http_trace.c')
bpf_tcp = BPF(src_file='tcp_trace.c')
bpf_udp = BPF(src_file='udp_trace.c')
bpf_dns = BPF(src_file='dns_trace.c')

# Define BPF perf output handlers
http_events = bpf_http['http_events']
tcp_events = bpf_tcp['tcp_events']
udp_events = bpf_udp['udp_events']
dns_events = bpf_dns['dns_events']

# Kafka producer function
def send_to_kafka(topic, data):
    producer.produce(topic, json.dumps(data).encode('utf-8'))
    producer.flush()

# Event handler functions
def handle_http_event(cpu, data, size):
    event = bpf_http["http_events"].event(data)
    send_to_kafka(http_topic, {'pid': event.pid, 'msg_len': event.msg_len})

def handle_tcp_event(cpu, data, size):
    event = bpf_tcp["tcp_events"].event(data)
    send_to_kafka(tcp_topic, {'pid': event.pid, 'saddr': event.saddr, 'daddr': event.daddr, 'sport': event.sport, 'dport': event.dport})

def handle_udp_event(cpu, data, size):
    event = bpf_udp["udp_events"].event(data)
    send_to_kafka(udp_topic, {'pid': event.pid, 'saddr': event.saddr, 'daddr': event.daddr, 'sport': event.sport, 'dport': event.dport})

def handle_dns_event(cpu, data, size):
    event = bpf_dns["dns_events"].event(data)
    send_to_kafka(dns_topic, {'pid': event.pid, 'query_domain': event.query_domain.decode('utf-8'), 'response_time_ns': event.response_time_ns})

# Attach BPF programs to perf output handlers
http_events.open_perf_buffer(handle_http_event)
tcp_events.open_perf_buffer(handle_tcp_event)
udp_events.open_perf_buffer(handle_udp_event)
dns_events.open_perf_buffer(handle_dns_event)

# Main loop to poll events
print("Starting to collect metrics...")
while True:
    try:
        bpf_http.perf_buffer_poll()
        bpf_tcp.perf_buffer_poll()
        bpf_udp.perf_buffer_poll()
        bpf_dns.perf_buffer_poll()
    except KeyboardInterrupt:
        print("Exiting...")
        break
