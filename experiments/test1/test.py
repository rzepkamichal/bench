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



def kill_handler(*args):
    """Handles keyboard interrupts (SIGINT) and termination signals (SIGTERM).

    Prints a cleanup message and exits the program.
    """
    print(Fore.RED + "Stop")
    sys.exit(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, kill_handler)
    signal.signal(signal.SIGTERM, kill_handler)

    print(Fore.RED + "Starting")

    while True:
        print(Fore.GREEN + "test")
        time.sleep(1)

    
       
