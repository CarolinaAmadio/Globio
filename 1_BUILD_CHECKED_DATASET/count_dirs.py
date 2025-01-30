import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    to count and print the number of netcdf in a dataset
    structred as floows: wmo/wmo_profile.nc
    ''', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(   '--input_dir','-i',
                                type = str,
                                required = False,
                                help = '''directory of the float_index.txt file''')

    return parser.parse_args()


args = argument()

return parser.parse_args()

import os
import pandas as pd

DATASET = (args.input_dir)
#DATASET = "/g100_work/OGS_devC/camadio/GLOBIO/SEANOE_SAUZ/SFILES_FINAL_v1"

def get_folders(path):
    folders = []
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            folders.append(dir_name)
        break  # Considera solo le sottocartelle immediate
    return folders

def count_nc_files(path):
    """Conta i file .nc in una directory e le sue sottodirectory."""
    count = 0
    for root, dirs, files in os.walk(path):
        count += sum(1 for file in files if file.endswith(".nc"))
    return count

n_ = count_nc_files(DATASET )
print("npropf : " + DATASET)
print(n_)

