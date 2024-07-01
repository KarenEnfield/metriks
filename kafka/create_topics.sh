#!/bin/bash

# Kafka broker address
KAFKA_BROKER="localhost:9092"

# List of topics to create
TOPICS=("http_metrics" "tcp_metrics" "udp_metrics" "dns_metrics")

# Create each topic
for TOPIC in "${TOPICS[@]}"; do
  docker-compose exec kafka kafka-topics.sh --create --topic $TOPIC --bootstrap-server $KAFKA_BROKER --partitions 1 --replication-factor 1
done

# chmod +x create_topics.sh
# ./create_topics.sh