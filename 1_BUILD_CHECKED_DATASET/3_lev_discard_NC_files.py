import sys
import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    mv files from CORIOLIS to DISCARDED DIRECTORY
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--outdir','-o',
                                type = str,
                                required = True,
                                help = 'path of the  dataset ')
    parser.add_argument(   '--input_dir','-i',
                                type = str,
                                required = False,
                                help = '''directory of the float_index.txt file''')
    parser.add_argument(   '--input_file','-ifile',
                                type = str,
                                required = False,
                                help = '''directory of the float_index.txt file''')
    return parser.parse_args()


args = argument()

import pandas as pd
import numpy as np
from netCDF4 import Dataset
import datetime
import os
import shutil
import sys

#INPUTDIR='/g100_scratch/userexternal/camadio0/GLOBIO/CORIOLIS/'
#OUTDIR ='/g100_scratch/userexternal/camadio0/GLOBIO/CORIOLIS/DISCARDED/'

#3_lev_discard_NC_files.py -i /g100_work/OGS_devC/camadio/GLOBIO/SEANOE_SAUZ//SFILES_FINAL_v2/ -o /g100_work/OGS_devC/camadio/GLOBIO/SEANOE_SAUZ//SFILES_FINAL_v2/discarded/ -ifile /g100_work/OGS_devC/camadio/GLOBIO/SEANOE_SAUZ//SFILES_FINAL_v2/Discarded_PresTemp_noteq_PresSal.csv

OUTDIR   = (args.outdir)
INPUTDIR = (args.input_dir)
ifile = os.path.join(INPUTDIR, args.input_file)

# crea acrtella se non esiste
if not os.path.exists(OUTDIR):
    os.makedirs(OUTDIR)


df= pd.read_csv( ifile )

list_files=df.Namefile.drop_duplicates()


for filename in list_files:
    file_to_remove = os.path.join(INPUTDIR, filename)
    target_path = os.path.join(OUTDIR, filename)
    if os.path.exists(file_to_remove ):  # outdir discarded/+ wmo+ file 
        print(f"Moving {file_to_remove} to {target_path}")
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # Move the file
        shutil.move(file_to_remove, target_path)
    else:
        print(f"File not found: {file_to_remove}") 

shutil.copy(ifile, OUTDIR)
shutil.copy('3_lev_discard_NC_files.py', OUTDIR)


