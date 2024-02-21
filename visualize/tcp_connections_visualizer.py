
import matplotlib.pyplot as plt
import networkx as nx
from kafka import KafkaConsumer, TopicPartition
import configparser
import os
import json
import math
import signal
import time
import pytz
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from kafka import __version__ as kafka_python_version

# Function to handle SIGINT (Ctrl-C)
exit_flag = False

def sigint_handler(signal, frame):
    global exit_flag
    exit_flag = True
    print("\nSIGINT received!")

def read_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)

    kafka_config = {
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', config.get('kafka_events_server', 'bootstrap_servers')),
        'topic': os.getenv('KAFKA_TOPIC', config.get('kafka_events_server', 'topic')),
        'group_id' : os.getenv('KAFKA_GROUP_ID', config.get('kafka_events_server', 'group_id')),
        'acks': os.getenv('KAFKA_ACKS', config.get('kafka_events_server', 'acks')),
        'auto_offset_reset': 'earliest',
        'api_version': tuple(map(int, os.getenv('KAFKA_API_VERSION', config.get('kafka_events_server', 'api_version')).split(','))),
        'commit': os.getenv('KAFKA_COMMIT', False),
        # Add more Kafka settings as needed
    }
    
    # Get the process_names from the tcp_event section in the config file
    # Override with environment variable if provided
    process_filter_str = os.getenv('PROCESS_FILTER', config.get('tcp_events', 'ignored_process_names', fallback=''))
    print(f"{process_filter_str}")

    # Convert the comma-separated string to a list, removing any empty strings
    process_filter_names = [name.strip() for name in process_filter_str.split(',') if name.strip()]
    
    
    # Set a boolean based on whether the list is empty or not
    process_filter_empty = all(name == "''" for name in process_filter_names)

    # Print the boolean value and the final list of process_names
    print(f'Is process_filter empty? {process_filter_empty}')
    print(f'Ignored process_names: {process_filter_names}')

    # Get the process_ports from the tcp_event section in the config file
    # Override with environment variable if provided
    exposed_ports_str = os.getenv('EXPOSED_PORTS', config.get('tcp_events', 'exposed_ports', fallback=''))
    print(f"{exposed_ports_str}")

    # Convert the comma-separated string to a list, removing any empty strings
    exposed_ports_names =  [int(num) for num in exposed_ports_str.split(',')]
    
    # Create the tcp_events_config dictionary
    tcp_events_config = {
        'streaming': os.getenv('DATA_STREAMING_ENABLED', config.getboolean('tcp_events', 'streaming', fallback=True)),
        'span_in_seconds': config.get('tcp_events','span_secs', fallback=2),
        'comm_filtering': not process_filter_empty,
        'ignored_process_names': process_filter_names,
        'exposed_ports': exposed_ports_names, 
        # Add more TCP event settings as needed
    }    
    
    if tcp_events_config.get('comm_filtering') is True :
        print(f"Comm Filter: {tcp_events_config.get('comm_filtering')} on Names: {tcp_events_config.get('process_names')}, Event Streaming: {tcp_events_config.get('streaming')}")

    return kafka_config, tcp_events_config

def create_kafka_consumer(kafka_config):
    consumer_config = {
        'bootstrap_servers': kafka_config['bootstrap_servers'],
        'group_id' : kafka_config['group_id'],
        'api_version': kafka_config['api_version'],
        'auto_offset_reset': 'earliest',  # Start consuming from the beginning of the topic
        'enable_auto_commit': kafka_config['commit'],  # Auto commit offsets
        # Add more Kafka consumer settings as needed
    }

    consumer = KafkaConsumer(kafka_config['topic'],**consumer_config)
    return consumer


try:
    #
    # Configuration setup from ini file/environment variables
    #
    # Read Kafka and TCP events configuration from the config file
    print("Create Kafka Config")
    kafka_config, tcp_events_config = read_config()
    print("Create Kafka Consumer")
    # Create Kafka consumer
    consumer = create_kafka_consumer(kafka_config)

    # Consumer success message
    print(f"Kafka consumer connected (Kafka python version {kafka_python_version} at {consumer.config['bootstrap_servers']})")

except Exception as e:
    print(f"Failed to create Kafka consumer: (Kafka python version {kafka_python_version}) {e}")
    exit(1)

#
#   Data Producing / BPF Event handling
#
TASK_COMM_LEN = 17  # Assuming the TASK_COMM_LEN value

consumer.subscribe(kafka_config['topic'])
 

# Set the desired time span
earliest_timestamp_ms = float('inf')
latest_timestamp_ms = float(0)

span_seconds = float(tcp_events_config['span_in_seconds'])

# Variables to store the first and last timestamps found in the range
first_timestamp_offset = None
last_timestamp_offset = None
last_partition = 0
first_offset = None
last_offset = None
last_topic = None

ignored_process_set = set(tcp_events_config['ignored_process_names'])
print(ignored_process_set)
exposed_ports_set = set(tcp_events_config['exposed_ports'])
print(f"{type(exposed_ports_set)},{exposed_ports_set}")

# Initialize a span graph
G = nx.DiGraph()
H = nx.MultiDiGraph()

kGraphMax = 25  # maximum edges to display
edge_count = 0 
multi_edge_count = 0

# Initialize a defaultdict with int as the default factory function
node_count_map = defaultdict(int)
map_package_names = defaultdict(int)

print(f"{span_seconds} sec span from: {kafka_config['topic']}")

try :
    # Consume messages for span_seconds
    start_time = time.time()
    while not exit_flag:

        elapsed_time = time.time() - start_time
        if elapsed_time>span_seconds:
            exit_flag = True
            break

        messages = consumer.poll(timeout_ms=500)  # Adjust the timeout as needed

        if messages is None:
            print('...waiting for more messages')
            continue


        for topic_partition, records in messages.items():     
            last_partition = topic_partition       
            for record in records:
                # Process the record
                # Check if the record is empty
                if not record:
                    print ('Warning: Message record is empty')
                    continue
                
                # Extract the message timestamp
                earliest_timestamp_ms = min(earliest_timestamp_ms,record.timestamp)
                latest_timestamp_ms = max(latest_timestamp_ms,record.timestamp)

                # Is time elapsed
                if (latest_timestamp_ms-earliest_timestamp_ms)/1000.0 >= span_seconds:
                    print("Current span load complete; write report")
                    exit_flag = True
                    break    

                # Update the last processed offset
                last_offset = record.offset
                last_partition = record.partition
                last_topic = record.topic
                
                try:
                    
                    #
                    # Process data here
                    #
                    
                    # Parse JSON string to dictionary
                    data = json.loads(record.value)
                    
                    # Extract fields from the Python object
                    event_id = data.get('event_id')
                    if event_id==2:
                        dest_ip = data.get('src_ip')
                        src_ip = data.get('dest_ip')
                        dest_port = data.get('src_port')
                        src_port = data.get('dest_port')
                    else:
                        src_ip = data.get('src_ip')
                        dest_ip = data.get('dest_ip')
                        src_port = data.get('src_port')
                        dest_port = data.get('dest_port')
                    pid = data.get('pid')
                    ppid = data.get('ppid') 
                    timestamp_offset_ns = data.get('timeoffset_ns')
                    comm = data.get('comm')
                    pcomm = data.get('pcomm')
                    tcomm = data.get('tcomm')
                    container_name = data.get('container_name')
                    dest_name = data.get('dest_name')
                    
                    
                    if first_timestamp_offset is None:
                        first_offset=record.offset
                        first_timestamp_offset = int(timestamp_offset_ns/1e6)/1e3

                    last_timestamp_offset = int(timestamp_offset_ns/1e6)/1e3

                    # make sure time offset is a valid numeric value
                    if not isinstance(timestamp_offset_ns, (int)):
                        print("Event time offset is not a numeric value:", type(timestamp_offset_ns))
                        offset_ns = int(timestamp_offset_ns)
                        print(f"Converted timeoffset to {timestamp_offset_ns}")

                    if comm in ignored_process_set:
                        continue; # skip it
                    
                    # Concatenate values to create a unique edge identifier
                    src_id = f"{src_ip}_{src_port}" 
                    dest_id = f"{dest_ip}_{dest_port}"
                    if event_id == 1 :
                        edge_identifier = f"{comm}_tcp_sendmsg"
                    elif event_id == 2:  
                        edge_identifier = f"{comm}_tcp_recvmsg"
                    else:
                        edge_identifier = f"{comm}_tcp_unknown"    

                    multi_key = edge_identifier
                    
                    #
                    # Plot the edge on the graph
                    #
    
                    
                    # Check if the edge already exists
                    if G.has_edge(src_id, dest_id) is False:
                        # Create a new edge 
                        G.add_edge(src_id, dest_id, comm={comm})
                        print(f'add edge {edge_count+1}')
                        edge_count = edge_count + 1

                    # Update the timestamp for the existing edge
                    G[src_id][dest_id]['timestamp_ns'] = timestamp_offset_ns    
                        
                    # Check if the multi edge already exists
                    if H.has_edge(src_id, dest_id,key=multi_key) is True:
                        # Update edge with time 
                        H[src_id][dest_id][multi_key]["timestamp"] = timestamp_offset_ns
                        H[src_id][dest_id][multi_key]["count"] = H[src_id][dest_id][multi_key]["count"]+1
                    else:
                        # Edge doesn't exist, add it with timestamp
                        H.add_edge(src_id, dest_id, key=multi_key, timestamp=timestamp_offset_ns, count=1)
                        print(f'add multi edge {multi_edge_count+1}:{multi_key}')
                        multi_edge_count = multi_edge_count + 1

                    if comm in map_package_names:
                        map_package_names[comm] += 1
                    else:
                        map_package_names[comm] = 1    

                    # Update the timestamp for the nodes
                    if (G.has_node(src_id)) is False: 
                        H.add_node(src_id)
                        G.add_node(src_id) 
        
                    G.nodes[src_id]['timestamp_ns'] = timestamp_offset_ns
                    H.nodes[src_id]['timestamp_ns'] = timestamp_offset_ns
                    
                    if src_id in node_count_map:
                        node_count_map[src_id] += 1
                    else:
                        node_count_map[src_id] = 1    

                    if (G.has_node(dest_id)) is False:   
                        H.add_node(dest_id)       
                        G.add_node(dest_id)  
                        
                    G.nodes[dest_id]['timestamp_ns'] = timestamp_offset_ns
                    H.nodes[dest_id]['timestamp_ns'] = timestamp_offset_ns
                    
                    if dest_id in node_count_map:
                        node_count_map[dest_id] += 1
                    else:
                        node_count_map[dest_id] = 1    
                    
                    if src_port in exposed_ports_set or dest_port in exposed_ports_set:
                        print(f'Comm: {comm}, Src IP: {src_ip}, Dest IP: {dest_ip}, Src Port: {src_port}, Dest Port: {dest_port}, PID: {pid}, Func ID: {event_id}, Time offset: {timestamp_offset_ns}') 

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e} ; Skip {record.value}")
                except Exception as e:
                    print(f"Error processing data {e} ; Skip record : {record.value}")
                    continue

            if exit_flag is True:      
                break       

except KeyboardInterrupt as e:
    print(f"<Keyboad interrupt detected>")

except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")

finally:
      
    # Create a layout for the graph
    pos = nx.circular_layout(G)  # You can use other layout algorithms

    # Set a slightly bigger canvas
    fig, ax = plt.subplots(figsize=(11, 9))

    # Set up the figure
    #fig, ax = plt.subplots()

    # Draw nodes as small circles
    nx.draw_networkx_nodes(G, pos, node_size=100, node_color='skyblue', alpha=0.6, ax=ax)

    # Draw edges as lines connecting nodes
    nx.draw_networkx_edges(G, pos, width=1, edge_color='gray', ax=ax, arrows=True, connectionstyle='arc3,rad=0.1')

    # Draw labels if needed
    nx.draw_networkx_labels(G, pos, font_size=6, font_color='black', ax=ax)

    # Extract edge labels from the 'comm' attribute
    edge_labels = {(source, target): edge_attributes['comm'] for source, target, edge_attributes in G.edges(data=True)}
    
    # Add edge labels to the plot
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)
    
    # Customize plot
    try:
        title = f"Visualize {G.number_of_edges()} commands between {G.number_of_nodes()} TCP endpoints, {span_seconds} seconds, records:({first_offset}-{last_offset})"
        plt.title(title)
    except ValueError as e:
        print(f"Error: {e}")

    # plt.title(f"Visualize MetriKs: {edge_count} TCP send/recv endpoints (addr_port) ({datetime.fromtimestamp(mintime).strftime('%Y-%m-%d %H:%M:%S')}-{datetime.fromtimestamp(maxtime).strftime('%Y-%m-%d %H:%M:%S')})")
    plt.axis('off')
    plt.savefig('vision.png')
    plt.show()

    # Clear the current figure
    plt.clf()

    plt.figure()
    # Create a layout for the graph
    pos2 = nx.circular_layout(H)  # You can use other layout algorithms

    # Set a slightly bigger canvas
    fig, ax = plt.subplots(figsize=(11, 9))

    # Draw the nodes
    # Draw nodes as small circles
    nx.draw_networkx_nodes(H, pos2, node_size=100, node_color='skyblue', alpha=0.6, ax=ax)

    # Draw edges as lines connecting nodes
    nx.draw_networkx_edges(H, pos2, width=1, edge_color='gray', ax=ax, arrows=True, connectionstyle='arc3,rad=0.1')
    
    # Extract edge labels from the 'comm' attribute
    edge_labels2 = {}
    for i, j, k, data in H.edges(keys=True, data=True):
        if 'count' in data:
            edge_labels2[(i, j, k)] = f"{k}({data['count']})"
        else:
            edge_labels2[(i, j, k)] = k

    # Staggered positions along the edge
    label_positions = [0.0, 0.1, 0.2, 0.3, 0.4]
    z=0
    # Draw staggered edge labels
    for (i, j, k), label in edge_labels2.items():
        p = label_positions[z]
        x = (pos2[i][0]*(1 - p) + pos2[j][0]) / 2  # x-coordinate of label
        y = (pos2[i][1]*(1 - p) + pos2[j][1]) / 2  # y-coordinate of label
        ax.text(x, y, label, fontsize=7, verticalalignment='center', horizontalalignment='center', color='red')
        z = (z+1)%5
    
    # Draw node labels
    nx.draw_networkx_labels(H, pos2)

    title = f"Visualize {H.number_of_edges()} TCP commands between {H.number_of_nodes()} Sockets, {span_seconds} seconds, records:({first_offset}-{last_offset})"
    plt.title(title)

    plt.savefig("multiplot2.png")
    # Show the plot
    # plt.show()

    # Convert earliest timestamp to datetime and format it
    timestamp_datetime_utc = datetime.utcfromtimestamp(earliest_timestamp_ms / 1000.0)
    
    # Set the local time zone
    local_tz = pytz.timezone('America/Los_Angeles')  # Replace 'your_local_timezone' with your desired time zone

    # Convert UTC datetime to local time zone
    timestamp_datetime_local = timestamp_datetime_utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
        
    formatted_timestamp = timestamp_datetime_local.strftime('%Y-%m-%d %H:%M:%S')
    print(f"First Timestamp: {formatted_timestamp}")


    # Get the number of nodes and edges
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    print(f"Number of multi-edges: {multi_edge_count}")
    for pkg, pkg_count in map_package_names.items():
        print(f"{pkg}: {pkg_count}")

    try:
        if kafka_config['commit'] :
            print(f"Commit offsets: {first_offset}-{last_offset}")
            if last_partition is None or last_offset is None or last_topic is None:
                print("Nothing to commit")   
            else:    
                # Create a TopicPartition object and seek to the last processed offset + 1
                tp = TopicPartition(last_topic, last_partition)
                consumer.seek(tp,last_offset+1)
                # Commit offsets
                consumer.commit()
        else:
            print(f"Processed offsets: {first_offset}-{last_offset}")        

    except Exception as err:
        print(f"Unexpected excpetion on commit: {err=}, {type(err)=}")
    finally:
        # Close Kafka consumer
        consumer.close()
        print("Exiting")
    
    # Close Kafka consumer
    #consumer.close()
    #print("Exiting")

