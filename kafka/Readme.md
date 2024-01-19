# Kafka Installation For Docker

This is to run Kafka in a docker container for use by eBPF data processor

Instructions were found here:  
    https://hub.docker.com/r/ubuntu/kafka

Install zookeeper for docker first
    % docker run -d -p 2181:2181 ubuntu/zookeeper:edge

Install Kafka for docker
    % docker run -d --name kafka-container -e TZ=UTC -p 9092:9092 -e ZOOKEEPER_HOST=host.docker.internal ubuntu/kafka:3.1-22.04_beta
