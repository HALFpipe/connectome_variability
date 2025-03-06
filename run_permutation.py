import numpy as np
import xarray as xr
import scipy.stats
import argparse
import os

def permute_and_compute_wasserstein(ds: xr.Dataset) -> xr.Dataset:
    """
    Randomly shuffles the version labels (fm20, fm24) across iterations.
    Computes the Wasserstein difference between distributions with shuffled version labels.

    Returns:
        xr.Dataset: An xarray dataset containing Wasserstein distances for each (cell, pipeline, subject).
    """
    subjects = ds.subject.values
    pipelines = ds.pipeline.values
    num_cells = ds.functional_connectivity.shape[0]

    # Permute labels
    permuted_ds = ds.copy(deep=True)  # Deep copy to avoid modifying the original dataset
    shuffled_labels = permuted_ds.iteration.values.copy()  # Copy original labels
    np.random.shuffle(shuffled_labels) #shuffle in place
    permuted_ds = permuted_ds.assign_coords(iteration=shuffled_labels)  #replace with shuffled labels

    # Array to store Wasserstein distances
    wasserstein_array = np.zeros((num_cells, len(pipelines), len(subjects)))

    for subject_idx, subject in enumerate(subjects): #subjects[:1]
        for pipeline_idx, pipeline in enumerate(pipelines):
            # Extract indices of fm20 and fm24 within the permuted dataset
            fm20_indices = np.where(permuted_ds.iteration.values == "fm20")[0]
            fm24_indices = np.where(permuted_ds.iteration.values == "fm24")[0]
            for cell_idx in range(num_cells):
                group_fm20 = permuted_ds.functional_connectivity[cell_idx, fm20_indices, pipeline_idx, subject_idx].values
                group_fm24 = permuted_ds.functional_connectivity[cell_idx, fm24_indices, pipeline_idx, subject_idx].values

                wasserstein_array[cell_idx, pipeline_idx, subject_idx] = scipy.stats.wasserstein_distance(group_fm20, group_fm24)

    wasserstein_ds = xr.Dataset(
        {"wasserstein_distance": (["cell", "pipeline", "subject"], wasserstein_array)},
        coords=dict(
            cell=permuted_ds.cell.values,
            pipeline=pipelines,
            subject=subjects
        ),
    )

    return wasserstein_ds


if __name__ == "__main__":
    # Parse SLURM array task ID
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_id", type=int, required=True, help="SLURM array task ID")
    parser.add_argument("--input_file", type=str, required=True, help="Path to the input NetCDF dataset")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save output files")
    args = parser.parse_args()
    task_id = args.task_id
    input_file = args.input_file
    output_dir = args.output_dir

    ds_combined = xr.open_dataset(input_file)
    wasserstein_ds = permute_and_compute_wasserstein(ds_combined)

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"permutation_{task_id}.nc")
    wasserstein_ds.to_netcdf(output_file, engine="netcdf4")

    print(f"Saved permutation results to {output_file}")
