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

    def build_args(self,repetition:int,time:datetime,task_name:str,name="benchmark") -> List[str]:
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
        return args


class Benchmark(BaseModel):
    """
    Configuration for a single benchmark scenario.
    """

    config: Config
    tasks: Dict[str,Task]

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


def run_benchmark(name):
    try:
        benchmark = parse_benchmark_config()
    except Exception as e:
        print(Fore.RED + "Couldn't parse config")
        print(e)
        kill_handler()
    
    time = datetime.datetime.now()
    for rep in range(benchmark.config.repetitions):        
#        try:
#            scripts = get_python_scripts()
#            print(Fore.GREEN + f"found the folowing scripts:\n {scripts}")
#        except Exception as e:
#            print(Fore.RED + "error in finding python Scripts")
#            print(e)
#            kill_handler()

        sleep(10)
        for task_name,task in benchmark.tasks.items():
            for _ in range(0, 5):
                print("Running task")
#                script_processes = []
                try:
                    cli_process = subprocess.Popen(task.command + task.build_args(rep,time,task_name,name,))
#                    for script in scripts:
#                        script_process = subprocess.Popen(['python3', script])
#                        script_processes.append(script_process)
                    cli_process.wait()
                    if(cli_process.returncode == 0):
                        break
                except Exception as e:
                    print(Fore.RED + "Couldn't start benchmark")
                    print(e)
                finally:
#                    for script_process in script_processes:
#                            script_process.kill()
                    sleep(10)
                    print(Fore.GREEN + "Retrying")       

#def get_python_scripts():
#    """Gets a list of Python scripts in the current working directory."""
#    return [file for file in os.listdir('.') if file.endswith('.py')]


def kill_handler(*args):
    print("\nCleaning up")
    sys.exit(1)

signal.signal(signal.SIGINT, kill_handler)
signal.signal(signal.SIGTERM, kill_handler)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <experiment_directory> <experiment_directory> ...")
        kill_handler()

    working_directory = os.getcwd()
    directories = sys.argv[1:]
    print(directories)
    for directory in directories:
        os.chdir(directory)
        folder_name = os.path.basename(directory)
        timeout = 60
        while True:
            try:
                run_benchmark(folder_name)
                break
            except Exception as e:
                print(Fore.CYAN + f"Retrying in {timeout / 60} min")
                sleep(timeout)
                timeout += 60


        os.chdir(working_directory)