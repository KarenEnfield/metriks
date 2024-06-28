# Use an appropriate base image with Python and necessary tools
FROM python:3.9-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    bpfcc-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install prometheus_client

# Copy the bpftrace script and Python script into the container
COPY httpcodes.bt /
COPY http_metrics.py /

# Expose Prometheus metrics port
EXPOSE 8000

# Run the Python script to start Prometheus server and capture metrics
CMD ["python", "http_metrics.py"]
