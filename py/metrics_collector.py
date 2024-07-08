import sys
print(sys.path)
from bcc import BPF
from kafka import KafkaProducer
import json
import socket
import signal
import struct

global exit_flag
exit_flag=False

#////////////////////////////////
# Create Signal Interrupt handling- SIGINT (Ctrl-C) to end collection
#
def sigint_handler(signal, frame):
    global exit_flag
    exit_flag = True
    print("\nSIGINT received! Exit")
    exit(1)
     
# Start the SIGINT handler
signal.signal(signal.SIGINT, sigint_handler)

#///////////////////////////////////////
# Setup Kafka Producer
#
# KAFKA TOPICS MUST EXIST FOR EACH EVENT
# 'tcp-events'
# 'udp-events'
# 'http-events'
# 'dns-events'
#/////////////////////////////////////////
kafka_broker = 'kafka-container:9092'

producer_config = {
    'bootstrap_servers': kafka_broker,
    'acks': 'all',
    'api_version': (0,11),
    # Add more Kafka producer settings as needed
}
producer = KafkaProducer(**producer_config)

#//////////////////////////////////////////////////////////
# Helper function to cache ip addresses to avoid DNS lookups
#///////////////////////////////////////////////////////////

# In-memory cache for DNS lookups
dns_cache = {}

def resolve_ip(ip):
    if ip in dns_cache:
        return dns_cache[ip]
    else:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            dns_cache[ip] = hostname
            return hostname
        except socket.herror:
            dns_cache[ip] = ip
            return ip


#/////////////////////////
# Begin Program Execution
#/////////////////////////

#////////////////////////////////////////
# Load BPF contents and assign bpf probes
#////////////////////////////////////////
print("open bpf events file")

# Read the content of the BPF program file
with open('bpf_events.c', 'r') as f:
    bpf_program_code = f.read()
print("load and attach all bpf events to probes")

# Compile and attach eBPF program
b = BPF(text=bpf_program_code)
b.attach_kprobe(event="tcp_v4_connect", fn_name="trace_tcp_connect")
b.attach_kprobe(event="udp_sendmsg", fn_name="trace_udp_sendmsg")
b.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")
b.attach_kprobe(event="dns_query", fn_name="trace_dns_query")

#/////////////////////////////////
# Callbacks to process bpf events
#/////////////////////////////////
def process_connect_event(cpu, data, size):
    global exit_flag
    if exit_flag==True:
        return
    event = b["connect_events"].event(data)
    saddr = socket.inet_ntoa(struct.pack("I", event.saddr))
    daddr = socket.inet_ntoa(struct.pack("I", event.daddr))
    event_dict = {
        "cmd":"tcp_connect",
        "pid": event.pid,
        "tgid": event.tgid,
        "saddr": resolve_ip(saddr),
        "daddr": resolve_ip(daddr),
        "sport": event.sport,
        "dport": event.dport,
        "latency": event.latency,
        "payload": event.payload.decode('utf-8', 'replace'),
        "comm": event.comm.decode('utf-8', 'replace'),
        "tcp_flags": event.flags,
        "window_size": event.window_size,
    }

    print(f"TCP connect event copied:{event.copied} s_port:{event.sport} d_port:{event.dport} comm:{event.comm} payload:{event.payload}")
        
    try: 
        producer.send('tcp-events', json.dumps(event_dict).encode('utf-8'))
    except Exception as err:
        print(f"Error on kafka producer 'tcp-events' send {err=}, {type(err)=}")
        exit_flag = True     

def process_tcp_event(cpu, data, size):
    global exit_flag
    if exit_flag==True:
        return
    event = b["tcp_events"].event(data)
    saddr = socket.inet_ntoa(struct.pack("I", event.saddr))
    daddr = socket.inet_ntoa(struct.pack("I", event.daddr))
    event_dict = {
        "cmd":"tcp_recvmsg",
        "pid": event.pid,
        "tgid": event.tgid,
        "saddr": resolve_ip(saddr),
        "daddr": resolve_ip(daddr),
        "sport": event.sport,
        "dport": event.dport,
        "latency": event.latency,
        "payload": event.payload.decode('utf-8', 'replace'),
        "comm": event.comm.decode('utf-8', 'replace'),
        "tcp_flags": event.flags,
        "window_size": event.window_size,
    }

    print(f"TCP recv event copied:{event.copied} s_port:{event.sport} d_port:{event.dport} comm:{event.comm} http_status:{event.http_status} pl:{event.payload}")
        
    try: 
        producer.send('tcp-events', json.dumps(event_dict).encode('utf-8'))
    except Exception as err:
        print(f"Error on kafka producer 'tcp-events' send {err=}, {type(err)=}")
        exit_flag = True     

def process_http_event(cpu, data, size):
    global exit_flag
    if exit_flag==True:
        return
    event = b["http_events"].event(data)
    saddr = socket.inet_ntoa(struct.pack("I", event.saddr))
    daddr = socket.inet_ntoa(struct.pack("I", event.daddr))
    event_dict = {
        "cmd":"tcp_recvmsg",
        "pid": event.pid,
        "tgid": event.tgid,
        "saddr": resolve_ip(saddr),
        "daddr": resolve_ip(daddr),
        "sport": event.sport,
        "dport": event.dport,
        "latency": event.latency,
        "comm": event.comm.decode('utf-8', 'replace'),
        "http_status": event.http_status,
        "payload": event.payload.decode('utf-8', 'replace')
    }
    
    print(f"HTTP recv event copied:{event.copied} s_port:{event.sport} d_port:{event.dport} comm:{event.comm} http_status:{event.http_status} pl:{event.payload} ") 
    
    try: 
        producer.send('http-events', json.dumps(event_dict).encode('utf-8'))
    except Exception as err:
        print(f"Error on kafka producer 'http-events' send {err=}, {type(err)=}")
        exit_flag = True     

def process_udp_event(cpu, data, size):
    global exit_flag
    if exit_flag==True:
        return
    event = b["udp_events"].event(data)
    saddr = socket.inet_ntoa(struct.pack("I", event.saddr))
    daddr = socket.inet_ntoa(struct.pack("I", event.daddr))
    event_dict = {
        "cmd":"udp_sendmsg",
        "pid": event.pid,
        "tgid": event.tgid,
        "saddr": resolve_ip(saddr),
        "daddr": resolve_ip(daddr),
        "sport": event.sport,
        "dport": event.dport,
        "latency": event.latency,
        "comm": event.comm.decode('utf-8', 'replace'),
        "payload": event.payload.decode('utf-8', 'replace')
    }
        
    print(f"UDP send event copied:{event.copied} s_port:{event.sport} d_port:{event.dport} comm:{event.comm} http_status:{event.http_status} payload:{event.payload}")

    try:
        producer.send('udp-events', json.dumps(event_dict).encode('utf-8'))
    except Exception as err:
        print(f"Error on kafka producer 'udp-events' send {err=}, {type(err)=}")
        exit_flag = True     


def process_dns_event(cpu, data, size):
    global exit_flag
    if exit_flag==True:
        return
    event = b["dns_events"].event(data)
    saddr = socket.inet_ntoa(struct.pack("I", event.saddr))
    daddr = socket.inet_ntoa(struct.pack("I", event.daddr))
    event_dict = {
        "cmd":"dns_query",
        "pid": event.pid,
        "tgid": event.tgid,
        "saddr": resolve_ip(saddr),
        "daddr": resolve_ip(daddr),
        "sport": event.sport,
        "dport": event.dport,
        "latency": event.latency,
        "comm": event.comm.decode('utf-8', 'replace')
    }

    print(f"DNS query event copied:{event.copied} s_port:{event.sport} d_port:{event.dport} comm:{event.comm}") 
    
    try:
        producer.send('dns-events', json.dumps(event_dict).encode('utf-8'))
    except Exception as err:
        print(f"Error on kafka producer 'dns-events' send {err=}, {type(err)=}")
        exit_flag = True    

#/////////////////////////////////
# Poll setup for event processing
#/////////////////////////////////
b["connect_events"].open_perf_buffer(process_connect_event)
b["tcp_events"].open_perf_buffer(process_tcp_event)
b["udp_events"].open_perf_buffer(process_udp_event)
b["http_events"].open_perf_buffer(process_http_event)
b["dns_events"].open_perf_buffer(process_dns_event)

#/////////////////////////////////
# Begin monitoring kernel with bpf
#/////////////////////////////////
print("Start monitoring bpf events...")

exit_flag = False

# Process data until KILL event
try:
    while not exit_flag:
        print("Poll for bpf data")
        b.perf_buffer_poll()
        
        if exit_flag:
            break

except Exception as err:
    print("Exiting...")
    
finally:
    #///////////////////////////////////////
    # Close Kafka producer and detach probes
    #///////////////////////////////////////
    print("Close Kafka producer and detach probes")
    producer.close()
    b.detach_kprobe(event="tcp_v4_connect")
    b.detach_kprobe(event="udp_sendmsg")
    b.detach_kprobe(event="tcp_recvmsg")
    b.detach_kprobe(event="dns_query")
    pass    
