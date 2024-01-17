# This specifies the Docker Desktop kernel as src
# FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc
# FROM docker/for-desktop-kernel:6.4.16-linuxkit as ksrc
FROM docker/for-desktop-kernel:6.4.2-pr-08bb04c5745bbb99edbaae00b6368d83123f1e7c as ksrc
FROM ubuntu:latest

# Install required packages#
WORKDIR /
COPY --from=ksrc /kernel-dev.tar /
RUN tar xf kernel-dev.tar && rm kernel-dev.tar

# Install linux tools & python
RUN apt-get update && \
    apt-get install -y \
        linux-headers-generic \
        build-essential \
        linux-tools-common \
        linux-tools-generic \
        kmod \
        python3-bpfcc \
        clang \
        llvm \
        bpfcc-tools \
        libelf-dev \
        && rm -rf /var/lib/apt/lists/*

#RUN apt-get update && \
#    apt-get install -y bpfcc-tools libbcc-examples llvm libelf-dev libssl-dev

# Install bcc Python bindings
#RUN pip install bcc python3-bpfcc
        
# RUN apt install -y kmod python3-bpfcc

# Set the working directory to /usr/src/app
#WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
#COPY . .

# Compile your program or perform other tasks
# ...


#COPY hello_world.py /root
#COPY metriks.py /root
COPY * /root
WORKDIR /root
CMD mount -t debugfs debugfs /sys/kernel/debug && /bin/bash
