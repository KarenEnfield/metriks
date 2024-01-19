# Stage 1: Kernel source stage
# Kernel version needed for docker ebpf
FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc

# Use a base image with the required dependencies
FROM ubuntu:latest

COPY --from=ksrc /kernel-dev.tar /
RUN tar xf kernel-dev.tar && rm kernel-dev.tar

# Install necessary packages for BPF compilation
RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libbpf-dev \
    python3 \
    python3-pip \
    linux-headers-generic \
    build-essential \
    linux-tools-common \
    linux-tools-generic \
    python3-bpfcc \
    bpfcc-tools \
    libelf-dev \
    kmod 

# Install Python dependencies
RUN pip3 install kafka-python networkx matplotlib

# Install bcc Python bindings
RUN pip install bcc pytest 

# Install utility
RUN pip install nano

# Copy Python scripts
# epbf data processing of tcp events logged to userspace, event data sent to kafka
COPY data_processing.py /app/data_processing.py
# ebpf tcp events logged to userspace, no kafka
COPY tcp_events.py /app/tcp_events.py
# common ebpf tcp event probes used by both scripts
COPY tcp_events.c /app/tcp_events.c
# shell script to run the python data processing script (uses Kafka Producer)
COPY dp.sh /app/dp.sh
RUN chmod +x /app/dp.sh

# Set the working directory
WORKDIR /app

CMD mount -t debugfs debugfs /sys/kernel/debug && /bin/bash
