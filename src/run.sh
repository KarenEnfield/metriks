#!/bin/bash

# ./run.sh -v EVENTS_HTTP_ONLY -val False -v ANOTHER_VARIABLE -val some_value

# Declare an associative array to store environment variable key-value pairs
declare -A env_vars

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -v|--variable)
      VAR_NAME="$2"
      shift # past argument
      shift # past value
      ;;
    -val|--value)
      VAR_VALUE="$2"
      shift # past argument
      shift # past value
      ;;
    *)
      # unknown option
      shift
      ;;
  esac

  # Store key-value pair in the associative array
  env_vars["$VAR_NAME"]="$VAR_VALUE"
done

# Set the environment variables
for key in "${!env_vars[@]}"; do
  export "$key=${env_vars[$key]}"
done

# Run your Python script
mkdir /lib/modules/6.6.12-linuxkit
chmod 777 /lib/modules/5.15.0-94-generic
ln -s /lib/modules/5.15.0-94-generic/build /lib/modules/6.6.12-linuxkit/build

python3 send_tcp_events.py
