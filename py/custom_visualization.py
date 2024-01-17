import matplotlib.pyplot as plt
import networkx as nx
from kafka import KafkaConsumer
import json

# Initialize Kafka consumer
consumer = KafkaConsumer('tcp_connections_topic', bootstrap_servers='kafka-server:9092')

# Initialize a directed graph
G = nx.DiGraph()

# Process data and update the graph
for message in consumer:
    data = json.loads(message.value)
    
    # Extract source and destination information
    src_ip = data['saddr']
    dst_ip = data['daddr']
    src_port = data['sport']
    dst_port = data['dport']

    # Add nodes and edges to the graph
    G.add_node(src_ip)
    G.add_node(dst_ip)
    G.add_edge(src_ip, dst_ip, label=f"{src_port} -> {dst_port}")

    # Plot the graph
    pos = nx.spring_layout(G)
    labels = nx.get_edge_attributes(G, 'label')
    nx.draw(G, pos, with_labels=True)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.show()
