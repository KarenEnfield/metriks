#!/bin/bash

# ./run.sh -v PROCESS_FILTER -val python3 -v ANOTHER_VARIABLE -val some_value

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

myenv/bin/python visualize.py

# Unset the environment variables
for key in "${!env_vars[@]}"; do
  unset "$key"
done
