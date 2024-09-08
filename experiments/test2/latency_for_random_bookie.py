import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import random
from http.client import HTTPConnection

from colorama import Fore, init

init(autoreset=True)  # Ensure automatic color reset


def introduce_latency(container_name, latency_ms):
    """Introduces network latency to a Docker container.

    Args:
        container_name (str): The name of the Docker container.
        latency_ms (int): The desired network latency in milliseconds.
    """

    try:
        container_id = subprocess.check_output(["docker", "inspect", "-f", "{{.Id}}", container_name]).decode('utf-8').strip()
        container_info = subprocess.check_output(["docker", "inspect", "-f", '{{json .NetworkSettings.Networks}}', container_name]).decode('utf-8')
        network_name = list(json.loads(container_info).keys())[0]
        network_details = subprocess.check_output(["docker", "network", "inspect", network_name]).decode('utf-8')

        print(network_details)
        # Extract IP address using regular expression
        match = re.search(r'IPAM.Config\[0\].IPPrefix.(.*?)/', network_details)
        if match:
            container_iface = match.group(1)
        else:
            raise Exception("Failed to parse IP prefix information")

        # Introduce latency on the container's interface
        subprocess.run(["tc", "qdisc", "add", "dev", container_iface, "root", "netem", "delay", f"{latency_ms}ms"])

        time.sleep(60)  # Adjust the delay time as needed

        # Remove network latency
        subprocess.run(["tc", "qdisc", "del", "dev", container_iface, "root"])

    except Exception as e:
        print(f"Error: {e}")



def get_bookie_names():
    """Retrieves a list of Bookie container names from Docker.
    """
    cmd = ["docker", "ps"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, _ = process.communicate()

    bookie_names = []
    for line in output.decode('utf-8').splitlines():
        if "apache/bookkeeper:latest" in line:
            bookie_name = line.split()[-1]
            bookie_names.append(bookie_name)

    return bookie_names


def kill_handler(*args):
    """Handles keyboard interrupts (SIGINT) and termination signals (SIGTERM).

    Prints a cleanup message and exits the program.
    """
    print("\nCleaning up...")
    sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, kill_handler)
    signal.signal(signal.SIGTERM, kill_handler)

    print(Fore.GREEN + "Starting introduce_latency")

    time.sleep(1)

    bookie_names = get_bookie_names()
    print( f"Found Bookie containers: {bookie_names}")

    
    while True:
        # Adjust interval and other parameters as needed for your test
        time.sleep(1)  # Adjust interval between stress periods

        # Choose a random Bookie
        bookie_to_stress = random.choice(bookie_names)
        introduce_latency(bookie_to_stress,10)

       
