# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -v|--variable)
      MY_VARIABLE="$2"
      shift # past argument
      shift # past value
      ;;
    *)
      # unknown option
      shift
      ;;
  esac
done

# Set the environment variable
export MY_VARIABLE="$MY_VARIABLE"
python3 visualize.py
