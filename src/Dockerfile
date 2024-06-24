# Stage 1: NOT NECESSARY: Obtain Kernel source stage if we needed to do a kernel build
# Ubuntu and Docker kernel versions should match
#
# List of ubuntu versions and their kernel versions
# https://askubuntu.com/questions/517136/list-of-ubuntu-versions-with-corresponding-linux-kernel-version
# List of Docker-for-Desktop kernel images
# https://hub.docker.com/r/docker/for-desktop-kernel/tags?page=1&ordering=last_updated
#
# Ubuntu 22:04 aka "Jammy Jellyfish" has 5.15.49-pr kernel support for running ebpf and Docker on a Mac
# FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc
#

# Use base image with the required dependencies: ie ubuntu:jammy aka "Jammy Jellyfish" aka ubuntu 22.04
FROM ubuntu:jammy

WORKDIR /

# Stage 1 continued for building a kernel image, not required!
# Copy kernel development tarball obtained from above
# COPY --from=ksrc /kernel-dev.tar /
# Extract 5.15.49-pr tarball to /app/myenv directory and clean up
# RUN tar xvf kernel-dev.tar && rm kernel-dev.tar

# No Kafka data production, only console output if this is uncommented
# ENV CONSOLE_NO_KAFKA

# Install dependencies for running eBPF programs in Docker on a MAC using python and C 
RUN apt-get update 

# Install python3-full for running the app and its dependencies in a venv, virtual environment
RUN apt-get install -y \    
    python3-full \
    && apt-get clean

# Install for writing python scripts that use bcc and bpf
RUN apt-get install -y \    
    kmod \
    python3-bpfcc \
    && apt-get clean

# Install docker-for-mac compatible headers, library modules, and tools     
RUN apt-get install -y \      
    linux-headers-generic \
    linux-tools-generic \
    linux-tools-common \
    && apt-get clean

    
# Other files for C-builds by bpf compiler  
RUN apt-get install -y \
    clang \
    llvm \
    libbpf-dev \
    build-essential \
    bpfcc-tools \
    && apt-get clean

# Dependencies for obtaining and building source code (optional)
RUN apt-get install -y \    
    libelf-dev \
    bc \   
    bpftrace \
    iproute2 \
    make \
    gcc \
    flex \
    bison \
    cmake \
    git \
    wget \
    libssl-dev \
    nodejs \
    && apt-get clean

# Monitoring tool for linux in 60 sec analysis
RUN apt-get install -y \
    sysstat \
    && apt-get clean

# Start python3 in a virtual environment.
# It is important to use python3 bcc installed previously
RUN python3 -m venv /app/myenv 

# Install application files and dependencies in the app subfolder 
WORKDIR /app 

# Capture the kernel version of docker-for-mac linux-headers installed previously
# and save to a temporary file for later usage when running the /app/run.sh script
RUN dpkg-query -W -f='${Version}' linux-headers-generic | cut -d'.' -f1-3 > /app/docker_kernel_version.txt

# Install Python dependencies in the virtual environment
RUN /app/myenv/bin/pip3 install kafka-python
RUN /app/myenv/bin/pip3 install pytest 
RUN /app/myenv/bin/pip3 install psutil 
RUN /app/myenv/bin/pip3 install docker 
RUN /app/myenv/bin/pip3 install nano   

# Set the environment variable to use the virtual environment bin folder to find utilities here first
ENV PATH="/app/myenv/bin:$PATH"

# Copy application code:

# ebpf event collection c-code
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


# Command to mount the file system will happen in the ./run.sh script
# CMD mount -t debugfs debugfs /sys/kernel/debug && /bin/bash
# CMD ["./run.sh"]
