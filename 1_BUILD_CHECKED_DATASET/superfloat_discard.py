import sys
import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    remove bad data where sal and tem no same lenght
    and modify the output
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--outdir','-o',
                                type = str,
                                required = True,
                                help = 'path of the Superfloat dataset ')
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


def write_report(filename, df_float_index):
    print(f"Processing file: {filename}")
    df_float_index = df_float_index[df_float_index[0] != filename]
    file_path = "Discarded_PresTemp_noteq_PresSal.csv"
    if not os.path.exists(file_path):
        df = pd.DataFrame({'Namefile': [filename]})
        df.to_csv(file_path, index=False)
    else:
        df = pd.read_csv(file_path)
        new_row = pd.DataFrame({'Namefile': [filename]})
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file_path, index=False)
    return df_float_index

#INPUTDIR='/g100_scratch/userexternal/camadio0/GLOBIO/CORIOLIS/'
#OUTDIR ='/g100_scratch/userexternal/camadio0/GLOBIO/'

OUTDIR = (args.outdir)
INPUTDIR= (args.input_dir)
input_file= INPUTDIR+ '/Float_Index.txt'
shutil.copy(input_file, input_file+'_bkp')

df_float_index= pd.read_csv( input_file  , header=None)

INDEX_FILE =  superfloat_generator.read_float_read_float_index(input_file)
nFiles     =  INDEX_FILE.size

VARLIST=['TEMP', 'TEMP_QC', 'TEMP_ADJUSTED', 'TEMP_ADJUSTED_QC', 'PSAL', 'PSAL_QC', 'PSAL_ADJUSTED', 'PSAL_ADJUSTED_QC'] 

for iFile in range(nFiles): # loop su tuttie le righe del float index
    timestr          = INDEX_FILE['date'][iFile].decode()
    lon              = INDEX_FILE['longitude' ][iFile]
    lat              = INDEX_FILE['latitude' ][iFile]
    filename         = INDEX_FILE['file_name'][iFile].decode()
    available_params = INDEX_FILE['parameters'][iFile].decode()
    parameterdatamode= INDEX_FILE['parameter_data_mode'][iFile].decode()
    float_time = datetime.datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')
    filename=filename.replace('coriolis/','').replace('profiles/','')
    if 'TEMP'  in available_params:
        p=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
        outfile = get_outfile(p, OUTDIR)
        print(outfile)
        try:
           nc = Dataset(INPUTDIR+'/'+filename)
           rejected=False
           for VAR in VARLIST:
               serv = nc.variables[VAR][:]
               # file type is ok
               if len(serv) > 0 and serv.dtype == np.dtype('float32'):
                  continue
               #verify some charatcer is empty 
               elif np.all(np.core.defchararray.equal(serv, b'')):
                  rejected=True 
                  df_float_index = write_report(filename, df_float_index)
                  break 
        
           if rejected: # some array in VARLIST is empty
              df_float_index = write_report(filename, df_float_index)           
        
           else:
              PresT, Temp, QcT = p.read('TEMP', read_adjusted=False)
              PresT, Sali, QcS = p.read('PSAL', read_adjusted=False)
              if len(Temp) != len(Sali):
                 # len mismatch btween temp and salinity 
                 df_float_index = write_report(filename, df_float_index)
        
        except OSError as e: #file corrotto
           rejected=True  
           df_float_index = write_report(filename, df_float_index)
           continue

df_float_index.reset_index(drop=True, inplace=True)
df_float_index.to_csv( INPUTDIR+ '/Float_Index.txt', header=False, index=False)

"""
df = pd.read_csv(infile, header=None)

for III in range(0,len(df)): 
    nc = Dataset(INPUTDIR+  df.iloc[III,0])  # 0 is the name of the first col
    #if (df.iloc[III,0]) == '5907063/SR5907063_003.nc':
    #    sys.exit()
    if 'TEMP' in nc.variables.keys() :
       TEMP=nc.variables['TEMP'][0,:]
       SAL=nc.variables['PSAL'][0,:]
       if len(TEMP) == len(SAL):
           pass
       else:
           print('eeeee')
           df.reset_index(drop=True, inplace=True)
           file_path = "Discarded_PresTemp_noteq_PresSal.csv"
           if not os.path.exists(file_path):
                 df = pd.DataFrame({'Namefile': [outfile]})
                 df.to_csv(file_path, index=False)
           else:
                 df = pd.read_csv(file_path)
                 new_row = pd.DataFrame({'Namefile': [outfile]})
                 df = pd.concat([df, new_row], ignore_index=True)
                 #df.to_csv(file_path, index=False)
           df = df.drop(III)
    nc.close()

df.reset_index(drop=True, inplace=True)
"""
