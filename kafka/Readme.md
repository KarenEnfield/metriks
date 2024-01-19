# Kafka Installation For Docker on MacOS

Run Kafka and Zookeeper in Docker containers on your MacOS 
(Apache Kafka 3.1.0 on Ubuntu 22.04 LTS	amd64, arm64, ppc64el, s390x architectures)

## Install and run Zookeeper on Docker (prerequisite)

    % docker run -d -p 2181:2181 ubuntu/zookeeper:edge

## Install and run Kafka on Docker

    % docker run -d --name kafka-container -e TZ=UTC -p 9092:9092 -e ZOOKEEPER_HOST=host.docker.internal ubuntu/kafka:3.1-22.04_beta

References: 
    https://hub.docker.com/r/ubuntu/kafka
