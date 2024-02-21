# Stage 1: Kernel source stage
# Kernel version needed for docker ebpf
# FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc
FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc
# Use a base image with the required dependencies
FROM ubuntu:latest

# FROM python:3.8-slim

COPY --from=ksrc /kernel-dev.tar /
RUN tar xf kernel-dev.tar && rm kernel-dev.tar

# COPY --from=ksrc /usr/src/linux /usr/src/linux

# No Kafka data production, only console output if this is uncommented
# ENV CONSOLE_NO_KAFKA

# Install necessary packages for BPF compilation
RUN apt-get update && apt-get install -y \
    clang \
    llvm \
    libbpf-dev \
    build-essential \
    linux-headers-generic \
    linux-tools-generic \
    kmod \
    bpfcc-tools \
    python3 \
    python3-bpfcc \
    python3-pip \
    libelf-dev \
    bcc \
    nodejs 
    
# Install Python dependencies
RUN pip3 install kafka-python

# Install bcc Python bindings
RUN pip3 install psutil docker nano   


# Copy Python scripts

# ebpf event collection

COPY bpf_tcp_events.c /app/bpf_tcp_events.c

# read ebpf tcp events and send them to a server
COPY send_tcp_events.py /app/send_tcp_events.py

# optional ebpf data logged to console, no kafka 
COPY console_display.py /app/console_display.py

# configuration file
COPY config.ini /app/config.ini

# shell script to begin sending events (uses Kafka Producer)
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# Set the working directory
WORKDIR /app

CMD mount -t debugfs debugfs /sys/kernel/debug && /bin/bash
