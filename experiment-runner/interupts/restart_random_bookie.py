import signal
import subprocess
import sys
import time
import random

from colorama import Fore, init

init(autoreset=True)  # Ensure automatic color reset

def restart_bookie(bookie_name):
    """Restarts a Bookie container using Docker.
    """
    try:
        subprocess.run(["docker", "restart", bookie_name])
        print(Fore.GREEN + f"Successfully restarted Bookie: {bookie_name}")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Error restarting Bookie {bookie_name}: {e}")


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

    print(Fore.GREEN + "Starting restart_bookie")

    bookie_names = get_bookie_names()
    print( f"Found Bookie containers: {bookie_names}")

    while True:
        # Adjust interval as needed
        time.sleep(30)

        try:
            bookie_to_restart = random.choice(bookie_names)
            restart_bookie(bookie_to_restart)
        except IndexError:
            print(Fore.RED + "No Bookie containers found. Exiting...")
            break


