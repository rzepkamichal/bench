import os
import sys
from typing import Any, Dict, List
import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel
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

class Benchmark(BaseModel):
    config: Any
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

    print("Config successfully read and validated.")

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
    axs[0, 0].legend(loc='best')

    # Plot Latency vs Throughput (Async)
    axs[0, 0].plot(mean_async_data['Tput (ops/sec)'], mean_async_data['95th p (ms)'], marker='o', linestyle='-')
    axs[0, 1].set_title('Latency vs Throughput (Async)')
    axs[0, 1].set_ylabel('Latency (ms) "95th p (ms)"')
    axs[0, 1].set_xlabel('Throughput (ops/sec)')
    axs[0, 1].legend(loc='best')

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


def get_data():

    files = os.listdir()

    if files is None or len(files) == 0:
        print("Experiment folder was empty")
        sys.exit(1)


    if ExperimentResult not in files:
        print("Experiment did not contain a ExperimentResult folder")
        sys.exit(1)

    tasks = get_task_parameters()

    os.chdir(ExperimentResult)
    files = os.listdir()

    if files is None or len(files) == 0:
        print("ExperimentResult folder was empty")
        sys.exit(1)

    files.sort(reverse=True)

    summary_csv_files = [file for file in files if file.endswith("summary.csv")]
    csv_files = [file for file in files if not (file.endswith("summary.csv") or file.endswith(".png"))]

    newest_summary_csv_file = summary_csv_files[0]
    newest_csv_file = csv_files[0]


    summary_csv_file = pd.read_csv(newest_summary_csv_file)
    output_file = newest_summary_csv_file.replace(".csv", ".png")

    plot_summary(summary_csv_file,tasks,output_file)
    csv_file = pd.read_csv(newest_csv_file)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot.py <experiment_directory> <experiment_directory> ...")
        sys.exit(1)

    working_directory = os.getcwd()
    directories = sys.argv[1:]
    print(directories)
    for directory in directories:
        os.chdir(directory)
        folder_name = os.path.basename(directory)
        get_data()
        os.chdir(working_directory)
