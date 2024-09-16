import argparse
import datetime
import os
import signal
import subprocess
import sys
from time import sleep
from typing import Dict, List
from tqdm import tqdm

from pydantic import BaseModel
import yaml

from colorama import Fore, init

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
    latency_correction: bool = True

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
        args.append("-lc")
        args.append(str(self.latency_correction))
        args.append("-zk")
        args.append(zk)
    
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


def run_benchmark(folder_name:str,zk:str):
    try:
        benchmark = parse_benchmark_config()
    except Exception as e:
        print(Fore.RED + "Couldn't parse config")
        print(e)
        kill_handler()
    
    time = datetime.datetime.now()
    for _ in range(benchmark.config.repetitions):        
#        try:
#            scripts = get_python_scripts()
#            print(Fore.GREEN + f"found the folowing scripts:\n {scripts}")
#        except Exception as e:
#            print(Fore.RED + "error in finding python Scripts")
#            print(e)
#            kill_handler()

#        sleep(10)
        for _,task in benchmark.tasks.items():
            for _ in range(0, 5):
                print("Running task")
#                script_processes = []
                try:
                    cli_process = subprocess.Popen(task.command + task.build_args(time=time,zk=zk,name=folder_name))
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


def retry_run_benchmark():
    timeout = 60
    for _ in range(0, 5):
        try:
            experiment_folder_name = os.path.basename(os.getcwd())
            run_benchmark(folder_name=experiment_folder_name, zk=zk)
            break
        except Exception as e:
            print(Fore.CYAN + f"Retrying in {timeout / 60} min")
            sleep(timeout)
            timeout += 60


def batch_traverse_and_cd(base_dir: str):
    abs_original_dir = os.path.abspath(os.getcwd())
    try:
        if not os.path.exists(base_dir):
            print(f"Error: folder for experiment batch {base_dir} dos not exist")
            sys.exit(1)
        os.chdir(base_dir)
        abs_base_dir = os.path.abspath(os.getcwd())
        subdirs = [subdir for subdir in os.listdir(abs_base_dir) if os.path.isdir(os.path.join(abs_base_dir, subdir))]
        for subdir in tqdm(subdirs,desc="Processing directories", unit="dir"):
            subdir_path = os.path.join(abs_base_dir, subdir)
            os.chdir(subdir_path)
            retry_run_benchmark()
            os.chdir(abs_base_dir)
                
    finally:
        os.chdir(abs_original_dir)

def list_travers_and_cd(dir_list: List[str]):
    working_directory = os.getcwd()
    for experiment_dir in tqdm(dir_list,desc="Processing directories", unit="dir"):
        if not os.path.exists(experiment_dir):
            print(f"Error: folder {experiment_dir} does not exist")
            continue
        os.chdir(experiment_dir)
        retry_run_benchmark()
        os.chdir(working_directory)


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

    if args.d is True:
        batch_dir  = args.directories[0]
        batch_traverse_and_cd(batch_dir)

    if args.d is False:
        list_dir = args.directories
        list_travers_and_cd(list_dir)