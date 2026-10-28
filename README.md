# Globio – ARGOPY Workflow

## Workflow management

The workflow is managed by `Launcher.sh`, which coordinates the execution of the operational scripts.

## Script organization

- **Numbered Python scripts** (e.g. `00_download_data_save_netcdf.py`): operational scripts that are part of the main workflow.
- **Optional check scripts** (e.g. `_ck_dataset_comparisons.py`): scripts used for validation, checks, and dataset comparisons. These files are not part of the standard workflow and can be executed independently when needed.

## Main files

| File | Description |
|---|---|
| `Launcher.sh` | Controls and coordinates the workflow execution. |
| `00_download_data_save_netcdf.py` | Downloads data and saves them in NetCDF format. |
| `_ck_dataset_comparisons.py` | Performs optional dataset comparison checks. |


