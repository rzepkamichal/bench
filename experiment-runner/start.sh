#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 <ip_list> <directory1> [<directory2> ...]"
    exit 1
fi

# Extract the IP list from the first parameter
ip_list="$1"
shift  # Remove the first parameter from the argument list

# Construct the directory list from the remaining parameters
dir_list=""
for dir in "$@"; do
    dir_list="$dir_list $dir"
done

# Run the Python script with the provided parameters
nohup python3 remotmain.py "$ip_list" $dir_list > ./output.log 2>&1 &

echo "Script started in background. Check output.log for details."

