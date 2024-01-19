# eBPF TCP Collector for Docker, with Kafka

Collects TCP-related events using eBPF kernel procesing in Docker and prints to userspace, with event data sent to by a producer to Kafka

## Option 1: eBPF tcp events & data processing, sent by Kafka Producer

    Install Kafka on Docker (See /kafka/Readme.md)

    Build the image with data processing for Kafka 
        % docker build -t ebpf-tcp-events -f Dockerfile .

    Run the container
        % docker run -it --rm --privileged -v /lib/modules:/lib/modules:ro -v /etc/localtime:/etc/localtime:ro --pid=host --name procesor-container ebpf-tcp-events


## Option 2: eBPF tcp events, no Kafka

    Build the image with event handling only (no event data sent to Kafka)
        % docker build -t ebpf-tcp-events -f DockerfileEH .

    Run the container 
        (same docker run command as in Option 1)  
              