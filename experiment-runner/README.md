### Installing Dependencies
   Install the required Python packages using `pip`:
```bash
pip install -r requirements.txt 
```
This will install all the necessary packages listed in `requirements.txt`.
            
## Running the Scripts    
            
### 1. Run Experiments
To run the experiments, use the `main.py` script. This script executes the experiments and saves the results.

```bash
python3 experiment-runner/src/main.py experiments/experiment1 experiments/experiment2
```

- `experiments/experiment1` is the directory containing the configuration or data for the experiments. Adjust this path as needed.

### 2. Plot Results

To plot the results from the experiments, use the `plot.py` script. This script generates visualizations based on the data produced by the experiments.

```bash
python3 experiment-runner/src/plot.py experiments/experiment1 experiments/experiment2
```

- `experiments/experiment1` is the directory containing the results of the experiments that you want to plot. Adjust this path as needed.

## Troubleshooting

- **Missing Dependencies:** If you encounter errors related to missing packages, ensure all dependencies are installed by running `pip install -r requirements.txt`.

- **File Not Found:** Verify that the paths to `experiments/...` are correct and that the files or directories exist.

- **Permissions Issues:** Ensure you have the necessary permissions to read from the input directories and write to the output directories.

