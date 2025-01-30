import sys
import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    remove bad data from Float_Index.txt where
    1- sal and tem no same lenght,
    2- vars are empty 
    3- corrupted files 
    Float_Index.txt overwritten but  copy is saved
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--outdir','-o',
                                type = str,
                                required = True,
                                help = 'path of the  dataset ')
    parser.add_argument(   '--input_dir','-i',
                                type = str,
                                required = False,
                                help = '''directory of the float_index.txt file''')
    
    parser.add_argument(   '--output_csv', '-outfile',
                                type = str,
                                required = True,
                                help = 'name of csv file in output eg discarded_vars_criteria_csv  ')
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
import sys

def get_outfile(p,outdir):
    wmo=p._my_float.wmo
    filename="%s%s/%s" %(outdir,wmo, os.path.basename(p._my_float.filename))
    return filename

def write_report(filename, df_float_index, motiv, OUTDIR, output_csv, first_var=None):
    print(f"Processing file: {filename}")

    df_float_index = df_float_index[df_float_index[0] != filename]

    # Crea o aggiorna il file CSV con una nuova riga contenente filename e motiv
    if not os.path.exists(output_csv):
        df = pd.DataFrame({'Namefile': [filename], 'Motiv': [motiv], 'FirstVar': [first_var]})
        df.to_csv(output_csv, index=False)
    else:
        df = pd.read_csv(output_csv)
        new_row = pd.DataFrame({'Namefile': [filename], 'Motiv': [motiv],'FirstVar': [first_var] })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(output_csv, index=False)

    return df_float_index


OUTDIR   = (args.outdir)
INPUTDIR = (args.input_dir)
output_csv = args.output_csv


input_file= INPUTDIR+ '/Float_Index.txt'
shutil.copy(input_file, input_file+'_0bkp')
df_float_index= pd.read_csv( input_file  , header=None)

INDEX_FILE =  superfloat_generator.read_float_read_float_index(input_file)
nFiles     =  INDEX_FILE.size

VARLIST=['TEMP', 'TEMP_QC', 'TEMP_ADJUSTED', 'TEMP_ADJUSTED_QC', 'PSAL', 'PSAL_QC', 'PSAL_ADJUSTED', 'PSAL_ADJUSTED_QC'] 
save_interval = 50000  # Save every 50,000 files
ICOUNT = 0

for iFile in range(nFiles):  # Loop su tutte le righe del float index
        timestr = INDEX_FILE['date'][iFile].decode()
        lon = INDEX_FILE['longitude'][iFile]
        lat = INDEX_FILE['latitude'][iFile]
        filename = INDEX_FILE['file_name'][iFile].decode()
        filename = filename.replace('coriolis/', '').replace('profiles/', '')
        available_params = INDEX_FILE['parameters'][iFile].decode()
        parameterdatamode = INDEX_FILE['parameter_data_mode'][iFile].decode()
        float_time = datetime.datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')

        # Controllo lat/lon
        BadPosition = (lon > 180.) or (lon < -180.) or (lat > 90.) or (lat < -90.)
        if BadPosition:
            motiv = 'latlon_fillvalue'
            df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv)
            continue

        # Controllo if TEMP 
        if 'TEMP' not in available_params:
            motiv = 'no_temp'
            df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv)
            continue

        p = bio_float.profile_gen(lon, lat, float_time, filename, available_params, parameterdatamode)
        outfile = get_outfile(p, OUTDIR)
        print(f"Processing: {outfile}")

        try:
            nc = Dataset(INPUTDIR + '/' + filename)
        except OSError:
            motiv = 'corrupted_nc'
            df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv)
            print(f"File corrotto: {filename}")
            continue  # Salta al prossimo file

        # Verifica vars
        skip_file = False
        for VAR in VARLIST:
            try:
                serv = nc.variables[VAR][:]
                if len(serv) > 0:
                    if VAR.endswith('_QC') and np.all(np.core.defchararray.equal(serv, b'')):
                        motiv = 'empty_var' + VAR
                        df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv, VAR)
                        skip_file = True
                        break
                else:
                    motiv = 'empty_var_' + VAR
                    df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv, VAR)
                    skip_file = True
                    break
            
            except Exception as e:
                motiv = 'NO_'+VAR
                df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv, VAR)
                print(f"Errore con variabile {VAR} nel file {filename}: {e}")
                skip_file = True
                break

        if skip_file: # se uno dei checks sopra ha segnalato un file da scartare
            continue  # skip_file=True → Salta al prossimo file 

        if 'TEMP' in available_params and 'PSAL' in available_params:
            PresT, Temp, QcT = p.read('TEMP', read_adjusted=False)
            PresT, Sali, QcS = p.read('PSAL', read_adjusted=False)
            if len(Temp) != len(Sali):
                motiv = 'lenTemp_lenSal'
                df_float_index = write_report(filename, df_float_index, motiv, OUTDIR, output_csv)
        else: 
            sys.exit('non dovrebbe entrare')
        ICOUNT += 1
        if ICOUNT % save_interval == 0:
            df_float_index.reset_index(drop=True, inplace=True)
            df_float_index.to_csv(INPUTDIR + f'/_partial_cleaned_Float_Index_{ICOUNT}.txt', header=False, index=False)
            print(f'Saved progress after {ICOUNT} files')


sys.exit()

df_float_index.reset_index(drop=True, inplace=True)
df_float_index.to_csv( input_file  , header=False, index=False)

