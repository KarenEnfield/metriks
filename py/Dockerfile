# Use an official Ubuntu base image
FROM ubuntu:jammy

# Set environment variables
# ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /

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
    curl \
    libssl-dev \
    nodejs \
    && apt-get clean

# Monitoring tool for linux in 60 sec analysis
RUN apt-get install -y \
    sysstat \
    && apt-get clean

# More Linux monitoring tools
RUN apt-get update && apt-get install -y ifstat iproute2 net-tools lsof tcpdump   

WORKDIR /app 
# Start python3 in a virtual environment.
# It is important to use python3 bcc installed previously
RUN python3 -m venv /app/myenv 

# Install application files and dependencies in the app subfolder 


# Capture the kernel version of docker-for-mac linux-headers installed previously
# and save to a temporary file for later usage when running the /app/run.sh script
RUN dpkg-query -W -f='${Version}' linux-headers-generic | cut -d'.' -f1-3 > /app/docker_kernel_version.txt

# Install Python dependencies in the virtual environment
RUN /app/myenv/bin/pip3 install git+https://github.com/dpkp/kafka-python.git

#RUN /app/myenv/bin/pip3 install kafka-python
RUN /app/myenv/bin/pip3 install pytest 
RUN /app/myenv/bin/pip3 install psutil 
RUN /app/myenv/bin/pip3 install docker 
RUN /app/myenv/bin/pip3 install nano   

# Set the environment variable to use the virtual environment bin folder to find utilities here first
ENV PATH="/app/myenv/bin:$PATH"
RUN export PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH"


# Copy eBPF C programs
COPY bpf_events.c /app/bpf_events.c
COPY http_event.c /app/http_event.c
COPY tcp_event.c /app/tcp_event.c
COPY udp_event.c /app/udp_event.c
COPY dns_event.c /app/dns_event.c
COPY my_tcphdr.h /app/my_tcphdr.h

# shell script to begin sending events (uses Kafka Producer)
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# Copy Python script
COPY metrics_collector.py /app/metrics_collector.py

# Capture the kernel version of docker-for-mac linux-headers installed previously
# and save to a temporary file for later usage when running the /app/run.sh script
RUN dpkg-query -W -f='${Version}' linux-headers-generic | cut -d'.' -f1-3 > /app/docker_kernel_version.txt

# Run the Python script
# CMD ["python3", "metrics_collector.py"]
