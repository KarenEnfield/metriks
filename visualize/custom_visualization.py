
import matplotlib.pyplot as plt
import networkx as nx
from kafka import KafkaConsumer
import json
import signal
import time
from datetime import datetime, timedelta
from kafka import __version__ as kafka_python_version

# Function to handle SIGINT (Ctrl-C)
exit_flag = False

def sigint_handler(signal, frame):
    global exit_flag
    exit_flag = True
    print("\nSIGINT received!")


# Initialize Kafka consumer
kafka_bootstrap_servers = 'kafka-container:9092'
tcp_connections_topic = 'tcp-events'
desired_api_version=(0, 11)
try:
    consumer_config = {
        'bootstrap_servers': ['kafka-container:9092'],  # Replace with your Kafka broker address
        'api_version': desired_api_version,
        'auto_offset_reset': 'earliest',  # Start consuming from the beginning of the topic
        'enable_auto_commit': True,  # Auto commit offsets
    }

    # Topic to consume messages from
    topic = 'tcp-events'  # Replace with your actual topic name

    # Create Kafka consumer instance
    consumer = KafkaConsumer(topic, **consumer_config)

except Exception as e:
    print(f"Failed to connect to Kafka ({kafka_python_version}) {e}")
    exit(1)


# Initialize a graph
# G = nx.DiGraph()
G = nx.Graph()
plt.show()

# Poll for messages, update the graph
while not exit_flag:
    messages = consumer.poll(timeout_ms=500)  # Adjust the timeout as needed
 
    current_time = datetime.now()
    # Iterate over edges and remove outdated ones
    for u, v, data in list(G.edges(data=True)):
        timestamp = data.get('timestamp', None)
        if timestamp is not None and current_time - timestamp > timedelta(minutes=5):
            G.remove_edge(u, v)

    # Iterate over nodes and remove outdated ones
    for node, data in list(G.nodes(data=True)):
        timestamp = data.get('timestamp', None)
        if timestamp is not None and current_time - timestamp > timedelta(minutes=5):
            G.remove_node(node)


    if messages is None:
        continue

    for topic_partition, records in messages.items():
        for record in records:
            # Process the record
            # Check if the record is empty
            if not record:
               continue
            try:
                # Parse JSON string to dictionary
                data = json.loads(record.value)
            
                # Extract fields from the Python object
                src_ip = data['src_ip']
                dest_ip = data.get('dest_ip')
                src_port = data.get('src_port')
                dest_port = data.get('dest_port')
                pid = data.get('pid')
                func_id = data.get('func_id')
                timestamp = data.get('timestamp')

                # Add nodes and edges to the graph
                #G.add_node(src_ip)
                #G.add_node(dest_ip)
                #G.add_edge(src_ip, dest_ip, label=f"{src_port} -> {dest_port}")
                #src_ip, dest_ip = connection

                # Add_or_update_edge(src_ip, src_port, dest_ip, dest_port):
                # Concatenate values to create a unique edge identifier
                edge_identifier = f"{src_ip}_{src_port}_{dest_ip}_{dest_port}"
                src_id = f"{src_ip}"
                dest_id = f"{dest_ip}"

                # G.add_node(src_id, timestamp=time.time())  # Add timestamp for each node
                # G.add_node(dest_id, timestamp=time.time())
                # Check if the edge already exists
                if G.has_edge(src_id, dest_id):
                    # Update the timestamp for the existing edge
                    G[src_id][dest_id]['timestamp'] = datetime.now()
                else:
                    # Create a new edge with the current timestamp
                    G.add_edge(src_id, dest_id, timestamp=datetime.now())
                
                # Update the timestamp for the nodes
                G.nodes[src_id]['timestamp'] = datetime.now()
                G.nodes[dest_id]['timestamp'] = datetime.now()

                # G.add_edge(src_ip, dest_ip)

                # Plot the graph
                #pos = nx.spring_layout(G)
                #labels = nx.get_edge_attributes(G, 'label')
                #nx.draw(G, pos, with_labels=True)
                #nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
                # plt.figure(figsize=(8, 6))
                G_directed = G.to_directed()
                pos = nx.spring_layout(G)  # You can choose a different layout if needed
                nx.draw(G, pos, with_labels=True, node_size=700, node_color='skyblue', font_size=8, font_color='black', font_weight='bold', arrowsize=10, edge_color='gray', linewidths=1)
                #nx.draw(G, pos, with_labels=True, node_size=700, node_color='skyblue', font_size=8, font_color='black', font_weight='bold', arrowsize=10, edge_color='gray', linewidths=1, connectionstyle='arc3,rad=0.1')
                plt.show()
                plt.savefig('vision.png')

                print(f'Src IP: {src_ip}, Dest IP: {dest_ip}, Src Port: {src_port}, Dest Port: {dest_port}, PID: {pid}, Func ID: {func_id}, Timestamp: {timestamp}') 
                

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e} ; Skip {record.value}")
            except Exception as e:
                print(f"Error processing data {e} ; Skip record : {record.value}")
                continue


# Close Kafka consumer

print("Exiting")
consumer.close()

