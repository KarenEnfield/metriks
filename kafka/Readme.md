# Kafka Installation For Docker on MacOS

Run Kafka and Zookeeper in Docker containers on your MacOS 
(Apache Kafka 3.1.0 on Ubuntu 22.04 LTS	amd64, arm64, ppc64el, s390x architectures)

## Install and run Zookeeper on Docker (prerequisite)
    Type:
        docker run -d -p 2181:2181 --name zookeeper ubuntu/zookeeper:edge

## Install and run Kafka on Docker

    Type:
        docker run -d --name kafka-container \
        -e TZ=UTC \
        -p 9092:9092 \
        -e ZOOKEEPER_HOST=host.docker.internal \
        -e ADVERTISED_LISTENERS=PLAINTEXT://kafka-container:9092,PLAINTEXT://localhost:9092 \
        -e KAFKA_BROKER_ID=1 \
        -e KAFKA_LOG_DIRS=/kafka-logs \
        ubuntu/kafka:3.1-22.04_beta

## Create topic tcp-events
    Type:
        docker exec kafka-container kafka-topics.sh \
        --create \
        --topic tcp-events \
        --bootstrap-server localhost:9092 \
        --partitions 1 \
        --replication-factor 1

## Troubleshooting
    Check the topic was created
        docker exec -it kafka-container kafka-topics.sh \
        --list \
        --bootstrap-server localhost:9092    
        
    Describe the topic
        docker exec -it kafka-container kafka-topics.sh --describe --topic tcp-events --bootstrap-server localhost:9092

    Delete the topic if necessary
        docker exec -it kafka-container kafka-topics.sh --zookeeper localhost:2181 --delete --topic tcp-events    

        docker exec -it kafka-container kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic tcp-events
    
    Write events
        docker exec -it kafka-container sh -c "kafka-console-producer.sh --topic tcp-events --bootstrap-server localhost:9092 <<EOF
This is my first event
This is my second event
This is my third event
EOF"

    Read the events
        docker exec -it kafka-container kafka-console-consumer.sh --topic tcp-events --from-beginning --bootstrap-server localhost:9092 


## References: 
    https://hub.docker.com/r/ubuntu/kafka
