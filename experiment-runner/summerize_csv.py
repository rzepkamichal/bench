import csv
import sys
from datetime import date, datetime
from typing import List, Optional
import pandas as pd
import os
import datetime

from pydantic import BaseModel, Field,ValidationError

SUMMARY = "-summary.csv"

class Experiment_result_name_format(BaseModel):
    experiment_time: str
    name: str
    
    @property
    def summary(self):
        return self.name.endswith(SUMMARY)

def parse_and_validate_name(input_string:str):
    parts = input_string.split('_')
    date_str, name = '_'.join(parts[:6]), '_'.join(parts[6:])

    datetime.datetime.strptime(date_str, '%Y_%m_%d_%H_%M_%S')
    
    data = Experiment_result_name_format(experiment_time=date_str, name=name)
    return data
    


class SummaryData(BaseModel):
    total_time: float = Field(..., gt=0)
    average_throughput: float = Field(..., gt=0)
    average_response_time: float = Field(..., gt=0)
    percentile_50: float = Field(..., gt=0)
    percentile_95: float = Field(..., gt=0)
    percentile_99: float = Field(..., gt=0)
    percentile_999: float = Field(..., gt=0)

def parse_and_validate_summary(file_path:str):
    """Parses and validates a summary CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        SummaryData: A validated SummaryData object.
    """

    data = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        # Assuming the first line is the header
        next(reader)
        for row in reader:
            try:
                # Convert values to floats
                row = [float(value) for value in row]
                summary_data = SummaryData(
                    total_time=row[0],
                    average_throughput=row[1],
                    average_response_time=row[2],
                    percentile_50=row[3],
                    percentile_95=row[4],
                    percentile_99=row[5],
                    percentile_999=row[6]
                )
                data.append(summary_data)
            except ValueError:
                print(f"Error parsing row: {row}")
                # Handle the error appropriately (e.g., skip the row, raise an exception)
            except Exception as e:
                print(f"Unexpected error: {e}")
                # Handle unexpected errors
    if len(data) > 1:
        print(f"Unexpected summary format multible lines {file_path}")
        print(f"{data[1:]}")
        sys.exit(1)
    if isinstance(data[0],SummaryData):
        return data[0]
    else:
        print(f"type error {data[0]}")
        sys.exit(1)
    

        


def load_csvs(experiment_result_name:Optional[Experiment_result_name_format]):
    """Loads a CSV files from current directory"""
    
    base_name = os.path.basename(os.getcwd())
    if base_name != "ExperimentResult":
        print(f"cwd is not ExperimentResult is is {base_name}")
        sys.exit(1)
    
    file_names = [str]
    try:
        file_names = os.listdir()
    except Exception:
        print("ExperimentResult dos not exist Experiment not Run?")
        sys.exit(1)
    matching_files = None
    if experiment_result_name is not None:
        matching_files = [f_name for f_name in file_names if f_name.startswith(experiment_result_name.experiment_time) and f_name.endswith(SUMMARY)]
    else:
        _summaries = [f_name for f_name in file_names if f_name.endswith(SUMMARY)]
        time_experiments = [(Experiment_result_name_format(summary_name).experiment_time,summary_name) for summary_name in _summaries if  summary_name.endswith(SUMMARY)]
        time_experiments.sort(key=0,reverse=True)

        last_exp = time_experiments[0][0]
        i:int
        for i,exp in enumerate(time_experiments):
            if last_exp != exp:
                break
            last_exp = exp

        experiments_list = [tup[1] for tup in time_experiments]
        matching_files = experiments_list[:i+1]

        print(f"found {matching_files[0]} to be the newest Experiment")

    if len(matching_files) == 0:
        print(f"no matiching experimt results found")
        sys.exit(1)

    summaries:List[SummaryData] = []
    for file in matching_files:
        summaries.append(parse_and_validate_summary(file))
    return summaries



def summarize(folder_name, experiment_result_name: Optional[Experiment_result_name_format]):
    try:
        os.chdir("ExperimentResult")
    except Exception:
        print(f"could not find ExperimentResult in {folder_name}")
        sys.exit(1)

    summaries = load_csvs(experiment_result_name)

    if not summaries:
        print("No summaries loaded")
        sys.exit(1)

    os.chdir('..')
    summary_data = []
    for i, summary in enumerate(summaries, start=1):
        summary_data.append([
            i,  # Exp ID
            '',  # async / sync
            '',  # thread num
            '',  # req num
            '',  # req size [B]
            summary.total_time,
            summary.average_throughput,
            summary.average_response_time,
            summary.percentile_50,
            summary.percentile_95,
            summary.percentile_99,
            summary.percentile_999
        ])

    columns = ['Exp ID', 'async / sync', 'thread num', 'req num', 'req size [B]', 'Total Time (sec)', 'Average Throughput (ops/sec)', 'Average Response Time (ms)', '50th p (ms)', '95th p (ms)', '99th p (ms)', '999th p (ms)']
    df = pd.DataFrame(summary_data, columns=columns)

    # Calculate summary statistics
    numeric_columns = df.columns[5:]  # Exclude non-numeric columns
    summary_stats = df[numeric_columns].agg(['mean', 'std']).round(3)
    summary_stats.index = ['avg', 'std dev']

    # Prepare the final DataFrame
    final_df = pd.concat([df, summary_stats])

    # Add the experiment name as the first row
    experiment_name = f"Experiment: {folder_name}"
    final_df = pd.concat([pd.DataFrame([['', '', '', '', '', '', '', '', '', '', '', '']], columns=columns, index=[experiment_name]), final_df])

    # Save to CSV
    output_file = f'{folder_name}.csv'
    final_df.to_csv(output_file, sep=';', index=True, index_label='')

    print(f"Summary saved to {output_file} in {os.getcwd()}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or  len(sys.argv) > 3 :
        print("Usage: python summarize_csv.py <experiment_directory> Optional<Experiment result name>")
        sys.exit(1)

    name = None
    if len(sys.argv) == 3:
        try:
            name_tmp = sys.argv[2]
            name = parse_and_validate_name(name_tmp)
        except ValidationError as e:
            print("<Experiment result name> has the wrong format")
            print(e)
            sys.exit(1)

    if name is None:
        print("no spesiffic Experiment given trying newest Experiment")

    directory = sys.argv[1]
    os.chdir(directory)
    folder_name = os.path.basename(directory)
    summarize(folder_name,name)