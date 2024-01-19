# metriks

Metriks observability program for tcp-related activity on a server

Observe TCP-related activity obtained through eBPF linux kernel filtering.
Linux kernel observations are from Docker containers on MacOS.

TCP observations are streamed as data to Kafka, also running in a Docker container on macOS

## Install Data processor / eBPF collector and Kafka processor data send
[Link to BPF README](./bpf/readme.md)

## Kafka Prerequisite (with Zookeeper)
[Link to Kafka README](./kafka/readme.md)
