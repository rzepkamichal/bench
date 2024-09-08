import os
import signal
import socket
import subprocess
import sys
import time
import random
from http.client import HTTPConnection

from colorama import Fore, init

init(autoreset=True)  # Ensure automatic color reset


def disconnect_and_reconnect(container_name):
    """Disconnects and reconnects a Docker container to a network.

    Args:
        container_name (str): The name of the Docker container.
    """

    folder_name = os.path.basename(os.getcwd())

    try:
        # Disconnect the container from the network
        subprocess.run(["docker", "network", "disconnect", f"{folder_name}_bookkeeper-internal", container_name])
        print(Fore.GREEN + f"Disconnected {container_name} from bookkeeper-internal")

        # Wait for one minute
        time.sleep(1)

        # Reconnect the container to the network
        subprocess.run(["docker", "network", "connect", f"{folder_name}_bookkeeper-internal", container_name])
        print(Fore.GREEN + f"Reconnected {container_name} to bookkeeper-internal")
    except Exception as e:
        print(Fore.RED + f"Error: {e}")
        kill_handler()



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

    print(Fore.GREEN + "Starting disconnect_and_reconnect")

    time.sleep(30)

    bookie_names = get_bookie_names()
    print( f"Found Bookie containers: {bookie_names}")

    
    while True:
        # Adjust interval and other parameters as needed for your test
        time.sleep(5)  # Adjust interval between stress periods

        # Choose a random Bookie
        bookie_to_stress = random.choice(bookie_names)
        disconnect_and_reconnect(bookie_to_stress)

       
