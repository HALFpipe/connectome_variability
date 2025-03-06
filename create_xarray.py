
import pickle
from pathlib import Path
import os
import numpy as np
from itertools import chain
from nilearn import datasets, plotting
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.axes import Axes
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap 
import nibabel as nib
import xarray as xr
import pandas as pd
import netCDF4


def create_xarray(data, fm_version):
    subjects = sorted(data.keys())
    pipelines = sorted(set(chain.from_iterable(d.keys() for d in data.values())))
    iterations = min(len(b) for a in data.values() for b in a.values())
    
    (k,) = set(
        chain.from_iterable(c.shape for a in data.values() for b in a.values() for c in b)
    )

    schaefer_atlas = datasets.fetch_atlas_schaefer_2018(
        n_rois=400, yeo_networks=7, resolution_mm=1
    )
    schaefer_atlas_labels = list(map(bytes.decode, schaefer_atlas["labels"]))
    indices = np.tril_indices(k, -1)
    labels = np.array(
        [
            f"{schaefer_atlas_labels[i]}, {schaefer_atlas_labels[j]}"
            for i, j in zip(*indices)
        ]
    )

    arrays = []
    version_labels = np.array([fm_version] * iterations)  # Assign "fm20" or "fm24"

    for subject in subjects:
        subject_arrays = []
        for pipeline in pipelines:
            array = np.dstack(data[subject][pipeline])[
                *indices, :iterations, np.newaxis, np.newaxis
            ]
            subject_arrays.append(array)
        
        subject_array = np.concatenate(subject_arrays, axis=2) #Stack across pipelines
        arrays.append(subject_array)

    array = np.concatenate(arrays, axis=3)  #Stack across subjects
    
    # Old approach with iteration+version labels
    iteration_labels = [f"{i}_{fm_version}" for i in range(iterations)] # define iteration labels globally  
    assert array.shape[1] == len(iteration_labels), (
        f"Iteration mismatch: data shape {array.shape[1]} vs labels {len(iteration_labels)}"
    )

    return xr.Dataset(
        {"functional_connectivity": (["cell", "iteration", "pipeline", "subject"], array)},
        coords=dict(
            cell=labels, 
            iteration=version_labels, 
            # other options are range(iterations) (naming=1,2,3...) or iteration_labels (naming=1_fm20, 2_fm20...)so on
            pipeline=pipelines, 
            subject=subjects,
            # version=("iteration", version_labels),  # This would categorize iterations into fm20 or fm24 by creating a sub-group
        ),
    )




## how to run:
# data_fm20 = pickle.load(open('fm20_feature-matrices.pkl', 'rb'))
# data_fm24 = pickle.load(open('fm24_feature-matrices.pkl', 'rb'))
# ds_fm20 = create_xarray(data_fm20, "fm20")
# ds_fm24 = create_xarray(data_fm24, "fm24")
# ds_combined = xr.concat([ds_fm20, ds_fm24], dim="iteration") # Merge datasets along the 'iteration' dimension
# ds_combined.to_netcdf("ds_combined.nc", engine="netcdf4")