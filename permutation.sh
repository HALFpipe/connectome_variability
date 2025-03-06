#!/bin/bash

#SBATCH --job-name=1000_permutations
#SBATCH --output=logs/permutation_%A_%a.out
#SBATCH --time=0-0:35:00    #? review 
#SBATCH --ntasks=1  
#SBATCH --cpus-per-task=60  #? review 
#SBATCH --mem=20G            #? review 
#SBATCH --array=1-100  # Runs 100 independent jobs
#SBATCH --partition=genoa

set -e
set -x

INPUT_FILE="/home/${USER}/ds_combined.nc"       # Input real dataset with fm20 and fm24 iterations 
OUTPUT_DIR="/home/${USER}/permutation_results"  
python run_permutation.py --task_id ${SLURM_ARRAY_TASK_ID} --input_file $INPUT_FILE --output_dir $OUTPUT_DIR
