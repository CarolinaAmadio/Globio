import sys
import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    remove bad data from Float_Index.txt where
    1- sal and tem no same lenght,
    2- vars are empty 
    3- corrupted files 
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--outdir','-o',
                                type = str,
                                required = True,
                                help = 'path of the  dataset ')
    parser.add_argument(   '--input_dir','-i',
                                type = str,
                                required = False,
                                help = '''directory of the float_index.txt file''')

    return parser.parse_args()


args = argument()

import pandas as pd
import numpy as np
from netCDF4 import Dataset
import superfloat_generator
import datetime
from bitsea.instruments import bio_float
import os
import shutil


def get_outfile(p,outdir):
    wmo=p._my_float.wmo
    filename="%s%s/%s" %(outdir,wmo, os.path.basename(p._my_float.filename))
    return filename


def write_report(filename, df_float_index, motiv, OUTDIR, first_var=None):
    print(f"Processing file: {filename}")

    df_float_index = df_float_index[df_float_index[0] != filename]
    file_path = "Discarded_profiles_csv"
    file_path=OUTDIR+ '/' + file_path

    # Crea o aggiorna il file CSV con una nuova riga contenente filename e motiv
    if not os.path.exists(file_path):
        df = pd.DataFrame({'Namefile': [filename], 'Motiv': [motiv], 'FirstVar': [first_var]})
        df.to_csv(file_path, index=False)
    else:
        df = pd.read_csv(file_path)
        new_row = pd.DataFrame({'Namefile': [filename], 'Motiv': [motiv],'FirstVar': [first_var] })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file_path, index=False)

    return df_float_index

#INPUTDIR='/g100_scratch/userexternal/camadio0/GLOBIO/CORIOLIS/'
#OUTDIR ='/g100_scratch/userexternal/camadio0/GLOBIO/'

OUTDIR   = (args.outdir)
INPUTDIR = (args.input_dir)


input_file= INPUTDIR+ '/Float_Index.txt'
shutil.copy(input_file, input_file+'_0bkp')
shutil.copy(input_file, input_file+'_1bkp')
shutil.copy(input_file, input_file+'_2bkp')

df_float_index= pd.read_csv( input_file  , header=None)

INDEX_FILE =  superfloat_generator.read_float_read_float_index(input_file)
nFiles     =  INDEX_FILE.size

VARLIST=['TEMP', 'TEMP_QC', 'TEMP_ADJUSTED', 'TEMP_ADJUSTED_QC', 'PSAL', 'PSAL_QC', 'PSAL_ADJUSTED', 'PSAL_ADJUSTED_QC'] 
save_interval = 50000  # Save every 50,000 files
ICOUNT = 0

for iFile in range(nFiles): # loop su tuttie le righe del float index
    timestr          = INDEX_FILE['date'][iFile].decode()
    lon              = INDEX_FILE['longitude' ][iFile]
    lat              = INDEX_FILE['latitude' ][iFile]
    filename         = INDEX_FILE['file_name'][iFile].decode()
    available_params = INDEX_FILE['parameters'][iFile].decode()
    parameterdatamode= INDEX_FILE['parameter_data_mode'][iFile].decode()
    float_time = datetime.datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')
    filename=filename.replace('coriolis/','').replace('profiles/','')
    if 'TEMP' not in available_params:
        motiv='no_temp'
        df_float_index = write_report(filename, df_float_index, motiv, OUTDIR)
        continue # prossimo file se Temp non c e

    p=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
    outfile = get_outfile(p, OUTDIR)
    print(outfile)
    skip_file = False
    try:
        nc = Dataset(INPUTDIR+'/'+filename)
        for VAR in VARLIST:
            serv = nc.variables[VAR][:]
            
            #data not empty and type ok
            if len(serv) > 0 and serv.dtype == np.dtype('float32'):
               continue

            #verify all charatcers  empty  in a var
            # alla prima variabile vuota eco dal ciclo 
            elif np.all(np.core.defchararray.equal(serv, b'')):
               motiv='empty_var'
               df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, VAR)
               skip_file = True
               break 

        if skip_file:
            continue

        PresT, Temp, QcT = p.read('TEMP', read_adjusted=False)
        PresT, Sali, QcS = p.read('PSAL', read_adjusted=False)
              
        # len mismatch btween temp and salinity
        if len(Temp) != len(Sali):
             df_float_index = write_report(filename, df_float_index, motiv, OUTDIR )
             motiv='lenTemp_lenSal'
        
    except OSError as e: #file corrotto
        motiv='corrupted_nc'
        df_float_index = write_report(filename, df_float_index, motiv, OUTDIR)
        continue

    ICOUNT += 1
    if ICOUNT % save_interval == 0:
        df_float_index.reset_index(drop=True, inplace=True)
        df_float_index.to_csv(INPUTDIR + f'/_partial_cleaned_Float_Index_{ICOUNT}.txt', header=False, index=False)
        print(f'Saved progress after {ICOUNT} files')

df_float_index.reset_index(drop=True, inplace=True)
df_float_index.to_csv( input_file  , header=False, index=False)

