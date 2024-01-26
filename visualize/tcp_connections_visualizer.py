
import matplotlib.pyplot as plt
import networkx as nx
from kafka import KafkaConsumer, TopicPartition
import configparser
import os
import json
import math
import signal
import time
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
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', config.get('kafka', 'bootstrap_servers')),
        'topic': os.getenv('KAFKA_TOPIC', config.get('kafka', 'topic')),
        'group_id' : os.getenv('KAFKA_GROUP_ID', config.get('kafka', 'group_id')),
        'acks': os.getenv('KAFKA_ACKS', config.get('kafka', 'acks')),
        'auto_offset_reset': 'earliest',
        'api_version': tuple(map(int, os.getenv('KAFKA_API_VERSION', config.get('kafka', 'api_version')).split(','))),
        'commit': os.getenv('KAFKA_COMMIT', False),
        # Add more Kafka settings as needed
    }
    
    # Get the process_names from the tcp_event section in the config file
    # Override with environment variable if provided
    process_names_env = os.getenv('PROCESS_NAMES_OVERRIDE', config.get('tcp_event', 'process_names', fallback=''))
    print(process_names_env)
    process_names_str = process_names_env

    # Convert the comma-separated string to a list, removing any empty strings
    process_names = [name.strip() for name in process_names_str.split(',') if name.strip()]
    

    # Set a boolean based on whether the list is empty or not
    process_names_empty = all(name == "''" for name in process_names)

    # Print the boolean value and the final list of process_names
    print(f'Is process_names empty? {process_names_empty}')
    print(f'Final process_names: {process_names}')

    # Create the tcp_event_config dictionary
    tcp_event_config = {
        'span_in_seconds': config.get('tcp_event','span_secs', fallback=2),
        'comm_filtering': not process_names_empty,
        'process_names': process_names,
        # Add more TCP event settings as needed
    }    

    # Read the 'enabled' value from the INI file and use the default of True
    data_streaming_config = {
        'enabled': os.getenv('DATA_STREAMING_ENABLED', config.getboolean('data_streaming', 'enabled', fallback=True)),
        # Add more data_streaming settings as needed
    }
    
    if tcp_event_config.get('comm_filtering') is True :
        print(f"Comm Filter: {tcp_event_config.get('comm_filtering')} on Names: {tcp_event_config.get('process_names')}, Data Stream: {data_streaming_config.get('enabled')}")

    return kafka_config, tcp_event_config, data_streaming_config

def create_kafka_consumer(kafka_config):
    consumer_config = {
        'bootstrap_servers': kafka_config['bootstrap_servers'],
        'group_id' : kafka_config['group_id'],
        'api_version': kafka_config['api_version'],
        'auto_offset_reset': 'earliest',  # Start consuming from the beginning of the topic
        'enable_auto_commit': False,  # Auto commit offsets
        # Add more Kafka consumer settings as needed
    }

    consumer = KafkaConsumer(kafka_config['topic'],**consumer_config)
    return consumer


try:
    #
    # Configuration setup from ini file/environment variables
    #
    # Read Kafka, TCP event, and data_streaming configuration from the config file
    print("Create Kafka Config")
    kafka_config, tcp_event_config, data_streaming_config = read_config()
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
TASK_COMM_LEN = 16  # Assuming the TASK_COMM_LEN value

consumer.subscribe(kafka_config['topic'])

# Set the desired time span
start_time = None
end_time = None
span_seconds = tcp_event_config['span_in_seconds']
time_span = timedelta(span_seconds)

# Variables to store the first and last timestamps found in the range
first_timestamp_offset = None
last_timestamp_offset = None
last_partition = None
process_set = set(tcp_event_config['process_names'])
print(process_set)

# Initialize a span graph
G = nx.DiGraph()

kGraphMax = 25  # maximum edges to display
edge_count = 0 

# Initialize a defaultdict with int as the default factory function
node_count_map = defaultdict(int)
map_package_names = defaultdict(int)

print(f"{time_span} sec span from: {kafka_config['topic']}")

try :
    # Consume messages for span_seconds
    while not exit_flag:

        messages = consumer.poll(timeout_ms=500)  # Adjust the timeout as needed
        
        # current_time = datetime.now()
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
                record_timestamp = datetime.utcfromtimestamp(record.timestamp / 1000)
                
                # Initialize start_time if not set
                if start_time is None:
                    start_time = record_timestamp
                    end_time = start_time + time_span

                # Is this out of the range
                if record_timestamp > end_time:
                    print("Current span load complete; write report")
                    exit_flag = True
                    break    

                last_record_offset = record.offset
                
                try:
                    
                    #
                    # Process data here
                    #
                    
                    # Parse JSON string to dictionary
                    data = json.loads(record.value)
                    
                    # Extract fields from the Python object
                    src_ip = data.get('src_ip')
                    dest_ip = data.get('dest_ip')
                    src_port = data.get('src_port')
                    dest_port = data.get('dest_port')
                    pid = data.get('pid')
                    func_id = data.get('func_id')
                    comm = data.get('comm')
                    timestamp_offset_ns = data.get('timeoffset_ns')
                    
                    if first_timestamp_offset is None:
                        first_timestamp_offset = int(timestamp_offset_ns/1e6)

                    last_timestamp_offset = int(timestamp_offset_ns/1e6)

                    # make sure time offset is a valid numeric value
                    if not isinstance(timestamp_offset_ns, (int)):
                        print("Event time offset is not a numeric value:", type(timestamp_offset_ns))
                        offset_ns = int(timestamp_offset_ns)
                        print(f"Converted timeoffset to {timestamp_offset_ns}")

                    if comm in process_set:
                        continue; # skip it
                    
                    # Concatenate values to create a unique edge identifier
                    edge_identifier = f"{pid}_{func_id}_{src_ip}_{src_port}_{dest_ip}_{dest_port}"
                    src_id = f"{src_ip}_{src_port}"
                    dest_id = f"{dest_ip}_{dest_port}"

                    #
                    # Plot the edge on the graph, if we have not exceeded the maximum edges
                    #
                    # if edge_count >= kGraphMax : # only plot a certain number of edges
                    #    print ('exit flag 1')
                    #    exit_flag = True
                    #    break;

                    
                    
                    # Check if the edge already exists
                    if G.has_edge(src_id, dest_id) is False:
                        # Create a new edge 
                        G.add_edge(src_id, dest_id, comm={comm})
                        print(f'add edge {edge_count+1}')
                        edge_count = edge_count + 1

                    map_package_names[comm] += 1

                    # Update the timestamp for the existing edge
                    G[src_id][dest_id]['timestamp_ns'] = timestamp_offset_ns    
                    
                    # Update the timestamp for the nodes
                    if (G.has_node(src_id)) is False: 
                        G.add_node(src_id) 
                        node_count_map[src_id] = 0
                         
                    G.nodes[src_id]['timestamp_ns'] = timestamp_offset_ns
                    node_count_map[src_id] += 1

                    if (G.has_node(dest_id)) is False:          
                        G.add_node(dest_id) 
                        node_count_map[dest_id] = 0   
                        
                    G.nodes[dest_id]['timestamp_ns'] = timestamp_offset_ns
                    node_count_map[dest_id] += 1
                    
                    # print(f'Comm: {comm}, Src IP: {src_ip}, Dest IP: {dest_ip}, Src Port: {src_port}, Dest Port: {dest_port}, PID: {pid}, Func ID: {func_id}, Time offset: {timestamp_offset_ns}') 

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e} ; Skip {record.value}")
                except Exception as e:
                    print(f"Error processing data {e} ; Skip record : {record.value}")
                    continue
        print('poll for more messages...')    

except KeyboardInterrupt as e:
    print(f"<Keyboad interrupt detected>")

except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")

finally:

    if (kafka_config['commit']):
        consumer.commit({TopicPartition(kafka_config['topic'], topic_partition): last_record_offset})   

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
    # Create a figure with a larger canvas
    try:
    # Your existing code to calculate mintime and maxtime
    # ...
        #pacific_time = timezone(timedelta(hours=-8))
        #print(f"Converted timestamp: {mintime} && {maxtime}")
        # Check if timestamps are within a reasonable range
        #if 0 < mintime < 2**31 and 0 < maxtime < 2**31:
        #    timestamp_datetime1 = datetime.fromtimestamp(end_timestamp_ns-span_ns, tz=pacific_time)
        #    timestamp_datetime2 = datetime.fromtimestamp(end_timestamp_ns, tz=pacific_time)
        #    timestamp_datetime1.strftime('%Y-%m-%d %H:%M:%S')
        #    timestamp_datetime2.strftime('%Y-%m-%d %H:%M:%S')


        title = f"Visualize TCP SocKets: {edge_count} TCP send/recv endpoints Span {span_seconds} secs T(0):+({first_timestamp_offset}-{last_timestamp_offset}) ms"
        plt.title(title)
        #else:
        #    print(f"Invalid timestamp values.{mintime} : {maxtime}")
    except ValueError as e:
        print(f"Error: {e}")
    # plt.title(f"Visualize MetriKs: {edge_count} TCP send/recv endpoints (addr_port) ({datetime.fromtimestamp(mintime).strftime('%Y-%m-%d %H:%M:%S')}-{datetime.fromtimestamp(maxtime).strftime('%Y-%m-%d %H:%M:%S')})")
    plt.axis('off')
    plt.savefig('vision.png')
    plt.show()

    # Get the number of nodes and edges
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    print(f"Number of nodes: {num_nodes}")
    print(f"Number of edges: {num_edges}")
    for pkg, pkg_count in map_package_names.items():
        print(f"{pkg}: {pkg_count}")

    # Close Kafka consumer
    consumer.close()
    print("Exiting")

