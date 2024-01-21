
from confluent_kafka import Consumer, KafkaError
import json

# Kafka consumer configuration
consumer_config = {
    'bootstrap.servers': 'kafka-container:9092',  # Replace with your Kafka broker address
    'group.id': 'my-consumer-group',  # Replace with your consumer group ID
    'auto.offset.reset': 'earliest',  # Start consuming from the beginning of the topic
}

# Topic to consume messages from
topic = 'tcp-events'  # Replace with your actual topic name

# Create Kafka consumer instance
consumer = Consumer(consumer_config)
consumer.subscribe([topic])

# Poll for messages
while True:
    msg = consumer.poll(1.0)  # Adjust the timeout as needed

    if msg is None:
        continue
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            continue
        else:
            print(msg.error())
            break
    try:
        
        print('Received message: {}'.format(msg.value().decode('utf-8')))
        data_str = msg.value.decode('utf-8')
        data = json.loads(data_str)
        src_ip = data['src_ip']
        dest_ip = data['dest_ip']
        src_port = data['src_port']
        dest_port = data['dest_port']
        pid = data['pid']
        func_id = data['func_id']
        timestamp = data['timestamp']
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
                        
# Close Kafka consumer
consumer.close()