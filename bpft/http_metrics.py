import subprocess
import time
from prometheus_client import start_http_server, Counter

# Start a Prometheus metrics server
start_http_server(8000)

# Define Prometheus Counters for HTTP codes
http_codes_counter = Counter('http_codes', 'Counts of HTTP status codes', ['status_code'])

# Function to parse bpftrace output and update Prometheus metrics
def update_metrics(output):
    for line in output.split('\n'):
        if line.startswith('HTTP Codes:'):
            continue
        parts = line.split(':')
        if len(parts) == 2:
            status_code = parts[0].strip()
            count = int(parts[1].strip())
            http_codes_counter.labels(status_code=status_code).inc(count)

# Function to run bpftrace script and process output
def run_bpftrace():
    process = subprocess.Popen(['bpftrace', 'httpcodes.bt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.read().decode('utf-8')
        if output:
            update_metrics(output)
        time.sleep(10)

if __name__ == '__main__':
    run_bpftrace()
