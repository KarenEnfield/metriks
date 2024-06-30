# Use an official Ubuntu base image
FROM ubuntu:jammy

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    bpfcc-tools \
    linux-headers-generic \
    clang \
    llvm \
    libelf-dev \
    iproute2 \
    iputils-ping \
    python3 \
    python3-pip \
    git \
    gcc \
    make \
    curl \
    net-tools \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install BCC and its Python bindings
RUN apt-get update && \
    apt-get install -y bpfcc-tools linux-headers-generic \
    python3-bpfcc \
    && rm -rf /var/lib/apt/lists/*

# Install confluent-kafka
# RUN pip3 install confluent-kafka
# Install python kafka
RUN pip3 install git+https://github.com/dpkp/kafka-python.git
#RUN pip3 install kafka-python

# Set working directory
WORKDIR /app

# Copy eBPF C programs
COPY http_trace.c /app/http_trace.c
COPY tcp_trace.c /app/tcp_trace.c
COPY udp_trace.c /app/udp_trace.c
COPY dns_trace.c /app/dns_trace.c

# Copy Python script
COPY metrics_collector.py /app/metrics_collector.py

# Capture the kernel version of docker-for-mac linux-headers installed previously
# and save to a temporary file for later usage when running the /app/run.sh script
RUN dpkg-query -W -f='${Version}' linux-headers-generic | cut -d'.' -f1-3 > /app/docker_kernel_version.txt

# Run the Python script
CMD ["python3", "metrics_collector.py"]
