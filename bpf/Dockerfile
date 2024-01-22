# Stage 1: Kernel source stage
# Kernel version needed for docker ebpf
FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc

# Use a base image with the required dependencies
FROM ubuntu:latest
# FROM python:3.8-slim

COPY --from=ksrc /kernel-dev.tar /
RUN tar xf kernel-dev.tar && rm kernel-dev.tar

# No Kafka data production, only console output if this is uncommented
# ENV CONSOLE_NO_KAFKA

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
    openjdk-11-jdk\
    netcat \ 
    telnet \
    iputils-ping \
    kmod 

# Install Python dependencies
RUN pip3 install kafka-python

# Install bcc Python bindings
RUN pip3 install bcc pytest 

# Copy Python scripts
# kafka producer of ebpf data
COPY data_producer.py /app/data_producer.py
# ebpf data logged to console, no kafka 
COPY console_display.py /app/console_display.py
# common ebpf event collection, used by both scripts
COPY bpf_collector.c /app/bpf_collector.c
COPY producer_settings.ini /app/producer_settings.ini
# shell script to run the python data processing script (uses Kafka Producer)
COPY dp.sh /app/run.sh
RUN chmod +x /app/run.sh

# Set the working directory
WORKDIR /app

CMD mount -t debugfs debugfs /sys/kernel/debug && /bin/bash
