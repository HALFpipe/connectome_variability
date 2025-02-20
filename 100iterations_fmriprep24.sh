#!/bin/bash

#SBATCH --job-name=100iterations

#SBATCH --output=100iterations_fmriprep24.%j.txt

#SBATCH --time=0-6

# Request half a node
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=120G

# Request temporary directory on the node itself
#SBATCH --constraint=scratch-node

# Run 100 iterations
#SBATCH --array=1-100

#SBATCH --partition=genoa

# Tell bash to exit the script if any command returns an error
set -e

# Print command as they're run
set -x

# Set up paths
source_path="/home/${USER}/confounds/host_updated"
target_directory="/home/${USER}/100iterations_fmriprep24"
cache_directory="/scratch-shared/${USER}/cache"
mkdir --parents "${target_directory}" "${cache_directory}"

# As we request a scratch-node, we can use the $TMPDIR environment variable
# to get a temporary directory on the node itself, which will be faster
working_directory=$(mktemp -d)

cat >"${working_directory}/license.txt" <<EOF
halfpipe@fmri.science
73053
 *C8FMo8yrzcZA
 FSCA7.lDgNIow
 e1n3o06osRFD3qtBRgsTy9f9bQHGOpY/riIUrHoEx5c=
EOF

basetemp_path="${working_directory}/basetemp"
mkdir --parents "${basetemp_path}"

echo "Using working directory for test ${working_directory}"

# Use --contain to not use default bind mounts in apptainer
# Use --cleanenv to avoid user environment variables affecting the run
# Bind the halfpipe source code path into the container, and use --cwd to
# run the command in that directory
# Bind the cache directory into the container, so that we can download
# test resources as needed, and cache them for future runs
# Bind the working directory so that we can set py.tests's basetemp
# and write all output files there
# Bind the home directory into the container for .gitconfig

# For performance, we remove the following py.test arguments that create 
# debug output `--verbose --full-trace --showlocals --log-cli-level="DEBUG"`

singularity exec --cleanenv --contain \
    --bind "${working_directory}/license.txt:/opt/freesurfer/license.txt" \
    --bind "${source_path}" \
    --cwd "${source_path}" \
    --bind "${cache_directory}:/var/cache" \
    --bind "${working_directory}" \
    --bind "${HOME}" \
    --bind "${TMPDIR}:/tmp" \
    halfpipe_fmriprep_24.sif \
    py.test \
    --basetemp "${basetemp_path}" \
    tests/workflows/test_consistency.py 

# Copy outputs to target directory while adding a unique suffix to the filename
find "${working_directory}" -name "*.zip" | while read -r zip_file; do
    cp --verbose \
        "${zip_file}" \
        "${target_directory}/$(basename "${zip_file}" .zip)_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.zip"
done

# Because we are using scratch-node storage, we don't need to clean up the
# working directory, as it will be automatically cleaned up by the scheduler
# when the job finishes
