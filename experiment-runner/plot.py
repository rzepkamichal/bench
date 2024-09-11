import argparse
import colorsys
import os
import sys
from typing import Any, Dict, List
import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm
import yaml

ExperimentResult = "ExperimentResult"
BENCHMARK = "benchmark.yml"

class Task(BaseModel):
    """
    Configuration for the workload generator.
    """
    command: Any
    throughput: int
    mode: str
    num_threads: int
    runtime: str
    payload_size: int
    task_id: int

class Config(BaseModel):
    name: str
    repetitions: int
    client: Any

class Benchmark(BaseModel):
    config: Config
    tasks: Dict[str, Task]



def get_task_parameters():
    """
    Reads a YAML file and validates it against the Benchmark schema.

    :param config_file_path: Path to the directory containing the YAML configuration file.
    :return: Benchmark object if validation is successful.
    """

    with open(BENCHMARK, "r") as file:
        config_data = yaml.safe_load(file)

    # Validate the data against the Benchmark schema
    config = Benchmark(**config_data)

    tasks_tp = []
    for (key,value) in config.tasks.items():
        if key == "warmup":
            continue

        tasks_tp.append((int(key[1:]),value))


    tasks_tp.sort()
    tasks = [item[1].__dict__ for item in tasks_tp]
    table = pd.DataFrame(tasks).drop(columns=['command'])

    desired_order = [
        'task_id',
        'mode',
        'throughput',
        'num_threads',
        'runtime',
        'payload_size'
    ]

    # Reorder the columns
    table = table[desired_order]
    return table


def plot_summary(file:pd.DataFrame, table:pd.DataFrame, output_file:str):
    fig, axs = plt.subplots(4, 2, figsize=(25, 15))
    fig.suptitle('Performance Metrics')

    # Add Run-ID to separate the same task in different runs
    if 'Run-ID' not in file.columns:
        file['Run-ID'] = (file.groupby('Task-ID').cumcount() + 1)

    # Select only numeric columns for the mean calculation
    numeric_cols = file.select_dtypes(include='number').columns

    # Split file into Async and Sync Tasks
    sync_data = file[file['async / sync'] == 'sync']
    async_data = file[file['async / sync'] == 'async']

    # Group by Task-ID and calculate the mean for each group
    mean_sync_data = sync_data.groupby('Task-ID').mean(numeric_only=True)
    mean_async_data = async_data.groupby('Task-ID').mean(numeric_only=True)

    # Plot Latency vs Throughput (Sync)
    axs[0, 0].plot(mean_sync_data['Tput (ops/sec)'], mean_sync_data['95th p (ms)'], marker='o', linestyle='-')
    axs[0, 0].set_title('Latency vs Throughput (Sync)')
    axs[0, 0].set_ylabel('Latency (ms) "95th p (ms)"')
    axs[0, 0].set_xlabel('Throughput (ops/sec)')
    axs[0, 0].legend([],loc='best')

    # Plot Latency vs Throughput (Async)
    axs[0, 0].plot(mean_async_data['Tput (ops/sec)'], mean_async_data['95th p (ms)'], marker='o', linestyle='-')
    axs[0, 1].set_title('Latency vs Throughput (Async)')
    axs[0, 1].set_ylabel('Latency (ms) "95th p (ms)"')
    axs[0, 1].set_xlabel('Throughput (ops/sec)')
    axs[0, 1].legend([],loc='best')

    # Plot Total Time
    for run_id, group in file.groupby('Run-ID'):
        axs[1, 0].plot(group['Task-ID'], group['Total Time (sec)'], marker='o', linestyle='-', label=f'Run {run_id}')
    axs[1, 0].set_title('Total Time')
    axs[1, 0].set_xlabel('Task-ID')
    axs[1, 0].set_ylabel('Total Time (sec)')
    axs[1, 0].legend(loc='best')

    # Plot Throughput
    for run_id, group in file.groupby('Run-ID'):
        axs[1, 1].plot(group['Task-ID'], group['Tput (ops/sec)'], marker='o', linestyle='-', label=f'Run {run_id}')
    axs[1, 1].set_title('Throughput')
    axs[1, 1].set_xlabel('Task-ID')
    axs[1, 1].set_ylabel('Throughput (ops/sec)')
    axs[1, 1].legend(loc='best')

    # Plot Response Time
    for run_id, group in file.groupby('Run-ID'):
        axs[2, 0].plot(group['Task-ID'], group['Resp. Time (ms)'], marker='o', linestyle='-', label=f'Run {run_id}')
    axs[2, 0].set_title('Response Time')
    axs[2, 0].set_xlabel('Task-ID')
    axs[2, 0].set_ylabel('Response Time (ms)')
    axs[2, 0].legend(loc='best')

    # Plot Percentiles
    for name, group in file.groupby('Task-ID'):
        axs[2, 1].plot(group['Task-ID'], group['50th p (ms)'], marker='_', markersize=15, linestyle='-', label='50th percentile' if name == 0 else "")
        axs[2, 1].plot(group['Task-ID'], group['95th p (ms)'], marker='_', markersize=15, linestyle='-', label='95th percentile' if name == 0 else "")
        axs[2, 1].plot(group['Task-ID'], group['99th p (ms)'], marker='_', markersize=15, linestyle='-', label='99th percentile' if name == 0 else "")
        axs[2, 1].plot(group['Task-ID'], group['999th p (ms)'], marker='_', markersize=15, linestyle='-', label='999th percentile' if name == 0 else "")
    axs[2, 1].set_yscale('log', base=10)
    axs[2, 1].set_title('Response Time Percentiles')
    axs[2, 1].set_xlabel('Task-ID')
    axs[2, 1].set_ylabel('Response Time (ms) log_10')
    axs[2, 1].legend(loc='best')


    # Add the table to the additional axis
    table_df = pd.DataFrame(table)
    axs[3, 0].axis("off")  
    axs[3, 1].axis("off")  
    axs[3, 1].table(cellText=table_df.values, colLabels=table_df.columns, cellLoc='center', loc='center')

    # Adjust layout and save the plot


    # Adjust layout and save the plot
    plt.tight_layout()  # Adjust rect to make space for the table
    try:
        plt.savefig(output_file)
        plt.close()
        print(f"Plot saved to {output_file}")
    except Exception as e:
        print(f"Error saving plot: {e}")





def plot_combined_summary(experiment_name_list: List[str],data_list: List[pd.DataFrame], output_file: str):

    fig, axs = plt.subplots(3, 2, figsize=(45, 30))
    fig.suptitle('Combined Performance Metrics Across Experiments')

    for (data, experiment_name) in zip(data_list, experiment_name_list):
        # Add Run-ID to separate the same task in different runs
        if 'Run-ID' not in data.columns:
            data['Run-ID'] = (data.groupby('Task-ID').cumcount() + 1)

        # Select only numeric columns for the mean calculation
        numeric_cols = data.select_dtypes(include='number').columns

        # Split file into Async and Sync Tasks
        sync_data = data[data['async / sync'] == 'sync']
        async_data = data[data['async / sync'] == 'async']

        # Group by Task-ID and calculate the mean for each group
        mean_sync_data = sync_data.groupby('Task-ID').mean(numeric_only=True)
        mean_async_data = async_data.groupby('Task-ID').mean(numeric_only=True)

        # Plot Latency vs Throughput (Sync)
        axs[0, 0].plot(mean_sync_data['Tput (ops/sec)'], mean_sync_data['95th p (ms)'], marker='o', linestyle='-', label=f'{experiment_name}')
        axs[0, 0].set_title('Latency vs Throughput (Sync)')
        axs[0, 0].set_ylabel('Latency (ms) "95th p (ms)"')
        axs[0, 0].set_xlabel('Throughput (ops/sec)')
        axs[0, 0].legend(loc='best')

        # Plot Latency vs Throughput (Async)
        axs[0, 1].plot(mean_async_data['Tput (ops/sec)'], mean_async_data['95th p (ms)'], marker='o', linestyle='-', label=f'{experiment_name}')
        axs[0, 1].set_title('Latency vs Throughput (Async)')
        axs[0, 1].set_ylabel('Latency (ms) "95th p (ms)"')
        axs[0, 1].set_xlabel('Throughput (ops/sec)')
        axs[0, 1].legend(loc='best')

        # Plot Total Time
        for run_id, group in data.groupby('Run-ID'):
            axs[1, 0].plot(group['Task-ID'], group['Total Time (sec)'], marker='o', linestyle='-', label=f'Run {run_id} ({experiment_name})')
        axs[1, 0].set_title('Total Time')
        axs[1, 0].set_xlabel('Task-ID')
        axs[1, 0].set_ylabel('Total Time (sec)')
        axs[1, 0].legend(loc='best')

        # Plot Throughput
        for run_id, group in data.groupby('Run-ID'):
            axs[1, 1].plot(group['Task-ID'], group['Tput (ops/sec)'], marker='o', linestyle='-', label=f'Run {run_id} ({experiment_name})')
        axs[1, 1].set_title('Throughput')
        axs[1, 1].set_xlabel('Task-ID')
        axs[1, 1].set_ylabel('Throughput (ops/sec)')
        axs[1, 1].legend(loc='best')

        # Plot Response Time
        for run_id, group in data.groupby('Run-ID'):
            axs[2, 0].plot(group['Task-ID'], group['Resp. Time (ms)'], marker='o', linestyle='-', label=f'Run {run_id} ({experiment_name})')
        axs[2, 0].set_title('Response Time')
        axs[2, 0].set_xlabel('Task-ID')
        axs[2, 0].set_ylabel('Response Time (ms)')
        axs[2, 0].legend(loc='best')

        # Plot Percentiles
        for name, group in data.groupby('Task-ID'):
            axs[2, 1].plot(group['Task-ID'], group['50th p (ms)'], marker='_', markersize=15, linestyle='-', label=f'50th ({experiment_name})' if name == 0 else "")
            axs[2, 1].plot(group['Task-ID'], group['95th p (ms)'], marker='_', markersize=15, linestyle='-', label=f'95th ({experiment_name})' if name == 0 else "")
            axs[2, 1].plot(group['Task-ID'], group['99th p (ms)'], marker='_', markersize=15, linestyle='-', label=f'99th ({experiment_name})' if name == 0 else "")
            axs[2, 1].plot(group['Task-ID'], group['999th p (ms)'], marker='_', markersize=15, linestyle='-', label=f'999th ({experiment_name})' if name == 0 else "")
        axs[2, 1].set_yscale('log', base=10)
        axs[2, 1].set_title('Response Time Percentiles')
        axs[2, 1].set_xlabel('Task-ID')
        axs[2, 1].set_ylabel('Response Time (ms) log_10')

    # Adjust layout and save the plot
    plt.tight_layout()
    try:
        plt.savefig(output_file)
        plt.close()
        print(f"Combined plot saved to {output_file}")
    except Exception as e:
        print(f"Error saving combined plot: {e}")


def get_data():
    files = os.listdir()

    experiment_name = os.path.basename(os.getcwd())

    if files is None or len(files) == 0:
        print(f"{ExperimentResult} was empty")
        return


    if ExperimentResult not in files:
        print(f"{ExperimentResult} not in {os.getcwd()}")
        return
    
    if BENCHMARK not in files:
        print(f"{BENCHMARK} not in {os.getcwd()}")
        return

    tasks = get_task_parameters()

    os.chdir(ExperimentResult)
    files = os.listdir()

    if files is None or len(files) == 0:
        print("ExperimentResult folder was empty")
        sys.exit(1)

    files.sort(reverse=True)

    summary_csv_files = [file for file in files if file.endswith("summary.csv")]
    #csv_files = [file for file in files if not (file.endswith("summary.csv") or file.endswith(".png"))]

    newest_summary_csv_file = summary_csv_files[0]
    #newest_csv_file = csv_files[0]


    summary_csv_file = pd.read_csv(newest_summary_csv_file)
    output_file = newest_summary_csv_file.replace(".csv", ".png")

    plot_summary(summary_csv_file,tasks,output_file)
    #csv_file = pd.read_csv(newest_csv_file)

    return experiment_name,summary_csv_file


def batch_traverse_and_cd(base_dir: str, fn):
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
            fn()
            os.chdir(abs_base_dir)
                
    finally:
        os.chdir(abs_original_dir)

def list_travers_and_cd(dir_list: List[str], fn):
    working_directory = os.getcwd()
    
    for experiment_dir in tqdm(dir_list,desc="Processing directories", unit="dir"):
        if not os.path.exists(experiment_dir):
            print(f"Error: folder {experiment_dir} does not exist")
            continue
        os.chdir(experiment_dir)
        fn()
        os.chdir(working_directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run plot script.")

    parser.add_argument('-d', action='store_true', help="Optional '-d' flag, indicates that only one directory is allowed.")
    parser.add_argument('-c', action='store_true', help="Optional '-d' plots a combined plot or not")
    parser.add_argument('directories', nargs='+', help="One or more experiment directories.")

    args = parser.parse_args()

    if args.d is True and len(args.directories) > 1:
        print("Usage: python plot.py -d <experiment_directory> <experiment_directory> ...")
        sys.exit(1)


    all_files = []

    if args.d is True:
        batch_dir = args.directories[0]
        batch_traverse_and_cd(batch_dir, lambda: all_files.append(get_data()))
    else:
        list_dir = args.directories
        list_travers_and_cd(list_dir, lambda: all_files.append(get_data()))

    if args.c is False:
        sys.exit(0)
    else:
        all_files = [file for file in all_files if file is not None]
        all_files = [(name,data) for name, data in all_files if name is not None and data is not None]


        experiment_name_list, data_list = zip(*all_files)

        output_file = "combined_plot.png"
        plot_combined_summary(list(experiment_name_list), list(data_list), output_file)
