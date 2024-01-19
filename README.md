# metriks

Metriks observability program for monitoring tcp-related activity

Data obtained through eBPF linux kernel filtering in a Docker container running on macOS

TCP observations are streamed as data to Kafka, also running in a Docker container on macOS

## Data Processor
[Link to BPF README](./bpf/Readme.md)

## Kafka Prerequisite (with Zookeeper)
[Link to Kafka README](./kafka/Readme.md)
