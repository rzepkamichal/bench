import argparse
import atexit
import builtins
import datetime
import os
import signal
import subprocess
import sys
from time import sleep
import time
from typing import Dict, List

from pydantic import BaseModel
import yaml

from colorama import Fore, Style, init

init(autoreset=True)  # Ensure automatic color reset

BENCHMARK = "benchmark.yml"


class Client(BaseModel):
    count: int


class Config(BaseModel):
    name: str
    repetitions: int
    client: Client


class Task(BaseModel):
    """
    Configuration for the workload generator.
    """

    command: List[str]
    throughput: int
    mode: str
    num_threads: int
    runtime: str
    payload_size: int
    task_id: int

    def build_args(self,time:datetime,zk:str,name:str) -> List[str]:

        """
        takes in the configuration and name and builds the cli args.
        """
        new_output_name = f'{time.strftime("%Y_%m_%d_%H_%M_%S")}_{name}'

        args = []
        args.append("-t")
        args.append(str(self.num_threads))
        args.append("-r")
        args.append(str(self.runtime))
        args.append("-p")
        args.append(str(self.payload_size))
        args.append("-l")
        args.append(str(self.throughput))
        args.append("-m")
        args.append(self.mode)
        args.append("-tid") 
        args.append(str(self.task_id))
        args.append("-o")
        args.append(new_output_name)
        args.append("-zk")
        args.append(zk)
        return args


class Benchmark(BaseModel):
    """
    Configuration for a single benchmark scenario.
    """

    config: Config
    tasks: Dict[str,Task]


def start_docker_containers(compose_file_path: str):
    """
    Start multiple containers using docker-compose.

    :param compose_file_path: Path to the docker-compose.yaml file.
    """
    return subprocess.run(
        ["docker", "compose", "-f", compose_file_path, "up", "-d"], check=True
    )


def stop_docker_containers(compose_file_path: str):
    """
    Stop multiple containers using docker-compose.

    :param compose_file_path: Path to the docker-compose.yaml file.
    """
    return subprocess.run(
        ["docker", "compose","-f", compose_file_path, "down"], check=True
    )


def parse_benchmark_config() -> Benchmark:
    """
    Reads a YAML file and validates it against the Benchmark schema.

    :param config_file_path: Path to the directory containing the YAML configuration file.
    :return: Benchmark object if validation is successful.
    """

    with open(BENCHMARK, "r") as file:
        config_data = yaml.safe_load(file)

    # Validate the data against the Benchmark schema
    config = Benchmark(**config_data)

    print(Fore.GREEN + "Config successfully read and validated.")
    return config


def run_benchmark(folder_name:str,zk:str):
    try:
        benchmark = parse_benchmark_config()
    except Exception as e:
        print(Fore.RED + "Couldn't parse config")
        print(e)
        kill_handler()
    
    time = datetime.datetime.now()
    for _ in range(benchmark.config.repetitions):
        try:
            start_docker_containers("docker-compose.yml")
        except Exception as e:
            print(Fore.RED + "Couldn't start containers")
            raise(e)
        
        try:
            scripts = get_python_scripts()
            print(Fore.GREEN + f"found the folowing scripts:\n {scripts}")
        except Exception as e:
            print(Fore.RED + "error in finding python Scripts")
            print(e)
            kill_handler()

        sleep(10)
        for _,task in benchmark.tasks.items():
            for _ in range(0, 5):
                print("Running task")
                script_processes = []
                try:
                    cli_process = subprocess.Popen(task.command + task.build_args(time=time,zk=zk,name=folder_name))
                    cli_process.wait()
                    if(cli_process.returncode == 0):
                        break
                except Exception as e:
                    print(Fore.RED + "Couldn't start benchmark")
                    print(e)
                finally:
                    for script_process in script_processes:
                            script_process.kill()
                    sleep(10)
                    print(Fore.GREEN + "Retrying")       

        try:
            stop_docker_containers("docker-compose.yml")
        except Exception as e:
            print(Fore.RED + "Couldn't stop containers")
            print(e)
        finally:
            kill_handler()

def get_python_scripts():
    """Gets a list of Python scripts in the current working directory."""
    return [file for file in os.listdir('.') if file.endswith('.py')]


def kill_handler(*args):
    print("\nCleaning up")
    try:
        stop_docker_containers("docker-compose.yml")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + "Cleaning up FAILED !!!")
    finally:
        sys.exit(1)

signal.signal(signal.SIGINT, kill_handler)
signal.signal(signal.SIGTERM, kill_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run benchmark script.")

    parser.add_argument('-d', action='store_true', help="Optional '-d' flag, indicates that only one directory is allowed.")
    parser.add_argument('zk', type=str, help="The zk string (required).")
    parser.add_argument('directories', nargs='+', help="One or more experiment directories.")

    args = parser.parse_args()
    zk = args.zk

    if args.d == "-d" and len(args.directories) > 1:
        print("Error: When using the '-d' flag, only one directory is allowed.")
        kill_handler()

    working_directory = os.getcwd()

    batch_dir  = args.directories[0]


    if args.d is True:

        if not os.path.exists(batch_dir):
            print(f"Error: folder for experiment batch {batch_dir} dos not exist")
            kill_handler()

        os.chdir(batch_dir)
        experiment_folders = os.listdir()


        for experiment_folder in experiment_folders:
            os.chdir(experiment_folder)
            experiment_folder_name = os.path.basename(experiment_folder)

            print(experiment_folder_name)
            timeout = 1

            while True:
                try:
                    run_benchmark(folder_name=experiment_folder_name, zk=zk)
                    break
                except Exception as e:
                    print(Fore.CYAN + f"Retrying in {timeout / 60} min")
                    sleep(timeout)
                    timeout += 60
            os.chdir(working_directory)

    if args.d is False:
        print("subfolde2122rs")
        for experiment_dir in args.directories:
            if not os.path.exists(experiment_dir):
                print(f"Error: folder {experiment_dir} dos not exist")
                kill_handler()
            os.chdir(experiment_dir)
            folder_name = os.path.basename(experiment_dir)
            timeout = 60

            while True:
                try:
                    run_benchmark(folder_name=folder_name, zk=zk)
                    break
                except Exception as e:
                    print(Fore.CYAN + f"Retrying in {timeout / 60} min")
                    sleep(timeout)
                    timeout += 60

            os.chdir(working_directory)