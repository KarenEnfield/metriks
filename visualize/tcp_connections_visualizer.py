
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
G = nx.DiGraph()

kGraphMax = 25
edge_count = 0
try :
    # Poll for messages, update the graph
    while not exit_flag:
        messages = consumer.poll(timeout_ms=500)  # Adjust the timeout as needed
    
        current_time = datetime.now()
        # Iterate over edges and remove outdated ones
        #for u, v, data in list(G.edges(data=True)):
        #    timestamp = data.get('timestamp', None)
        #    if timestamp is not None and current_time - timestamp > timedelta(minutes=5):
        #        G.remove_edge(u, v)

        # Iterate over nodes and remove outdated ones
        #for node, data in list(G.nodes(data=True)):
        #    timestamp = data.get('timestamp', None)
        #    if timestamp is not None and current_time - timestamp > timedelta(minutes=5):
        #        G.remove_node(node)


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
                    comm = data.get('comm')

                    # Concatenate values to create a unique edge identifier
                    edge_identifier = f"{src_ip}_{src_port}_{dest_ip}_{dest_port}"
                    src_id = f"{src_ip}_{src_port}"
                    dest_id = f"{dest_ip}_{dest_port}"

                    if src_port+dest_port+src_ip+dest_ip == 0 :
                        continue # skip
                    if src_ip==dest_ip :
                        continue
                    if edge_count >= kGraphMax :
                        continue
                    
                    timestamp = datetime.now()
                    
                    # Check if the edge already exists
                    if G.has_edge(src_id, dest_id) is False:
                        # Create a new edge 
                        G.add_edge(src_id, dest_id)
                        edge_count = edge_count + 1
                        

                    # Update the timestamp for the existing edge
                    G[src_id][dest_id]['timestamp'] = timestamp    
                    
                    # Update the timestamp for the nodes
                    if (G.has_node(src_id)) is False:
                        G.add_node(src_id) 
                    G.nodes[src_id]['timestamp'] = timestamp
                         
                    if (G.has_node(dest_id)) is False:          
                        G.add_node(dest_id)     
                    G.nodes[dest_id]['timestamp'] = timestamp

                    print(f'Comm: {comm}, Src IP: {src_ip}, Dest IP: {dest_ip}, Src Port: {src_port}, Dest Port: {dest_port}, PID: {pid}, Func ID: {func_id}, Timestamp: {timestamp}') 
                    
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e} ; Skip {record.value}")
                except Exception as e:
                    print(f"Error processing data {e} ; Skip record : {record.value}")
                    continue

except KeyboardInterrupt:
    
    
    
    # Create a layout for the graph
    pos = nx.circular_layout(G)  # You can use other layout algorithms

    # Set up the figure
    fig, ax = plt.subplots()

    # Draw nodes as small circles
    nx.draw_networkx_nodes(G, pos, node_size=100, node_color='skyblue', alpha=0.6, ax=ax)

    # Draw edges as lines connecting nodes
    nx.draw_networkx_edges(G, pos, width=1, edge_color='gray', ax=ax, arrows=True, connectionstyle='arc3,rad=0.1')

    # Draw labels if needed
    nx.draw_networkx_labels(G, pos, font_size=6, font_color='black', ax=ax)

    # Customize plot
    # Create a figure with a larger canvas
    plt.title(f"Visualize MetriKs: {edge_count} TCP send/recv endpoints (addr_port)")
    plt.axis('off')
    plt.savefig('vision.png')
    plt.show()

    # Get the number of nodes and edges
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")

    # Close Kafka consumer
    consumer.close()
    print("Exiting")

