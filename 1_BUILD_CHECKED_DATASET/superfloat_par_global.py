import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Creates superfloat files of downwelling PAR.
    Reads from Coriolis.
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--datestart','-s',
                                type = str,
                                required = False,
                                help = '''date in yyyymmdd format''')
    parser.add_argument(   '--dateend','-e',
                                type = str,
                                required = False,
                                help = '''date in yyyymmdd format ''')
    parser.add_argument(   '--outdir','-o',
                                type = str,
                                required = True,
                                default = "/gpfs/scratch/userexternal/gbolzon0/SUPERFLOAT/",
                                help = 'path of the Superfloat dataset ')
    parser.add_argument(   '--force', '-f',
                                action='store_true',
                                help = """Overwrite existing files
                                """)
    parser.add_argument(   '--update_file','-u',
                                type = str,
                                required = False,
                                default = 'NO_file',
                                help = '''file with updated floats''')
    return parser.parse_args()

args = argument()

if (args.datestart == 'NO_data') & (args.dateend == 'NO_data') & (args.update_file == 'NO_file'):
    raise ValueError("No file nor data inserted: you have to pass either datastart and dataeend or the update_file")

if ((args.datestart == 'NO_data') or (args.dateend == 'NO_data')) & (args.update_file == 'NO_file'):
    raise ValueError("No file nor data inserted: you have to pass both datastart and dataeend")


from bitsea.instruments import bio_float
from bitsea.commons.time_interval import TimeInterval
import superfloat_generator
from bitsea.commons.utils import addsep
import os
import scipy.io as NC
import numpy as np
import datetime
from netCDF4 import Dataset

class Metadata():
    def __init__(self, filename):
        self.filename = filename
        self.status_var = 'n'

def check_bgcvar_empty(outfile,VARNAME='DOWNWELLING_PAR' ):
    coriolis_file=outfile.replace('SUPERFLOAT','CORIOLIS')
    nc = Dataset(coriolis_file)
    VARLIST= [VARNAME + '_ADJUSTED',  VARNAME+ '_ADJUSTED_QC']
    listempty=[]
    for VAR in VARLIST:
        serv = nc.variables[VAR][:]
        if isinstance(serv, np.ma.MaskedArray):
           if np.all(np.ma.getdata(serv) == b'') or np.all(serv.mask):
              listempty.append(VAR)
           else:
              if np.all(serv == b''):
                 listempty.append(VAR)
    return len(listempty)>0

def dump_par_file(outfile, p, Pres, Value, Qc, metadata, mode='w'):
    nP=len(Pres)
    if mode=='a':
        command = "cp %s %s.tmp" %(outfile,outfile)
        os.system(command)
    ncOUT = NC.netcdf_file(outfile + ".tmp" ,mode)

    if mode=='w': # if not existing file, we'll put header, TEMP, PSAL
        setattr(ncOUT, 'origin'     , 'coriolis')
        setattr(ncOUT, 'file_origin', metadata.filename)
        PresT, Temp, QcT = p.read('TEMP', read_adjusted=False)
        PresT, Sali, QcS = p.read('PSAL', read_adjusted=False)        
        ncOUT.createDimension("DATETIME",14)
        ncOUT.createDimension("NPROF", 1)
        ncOUT.createDimension('nTEMP', len(PresT))
        ncOUT.createDimension('nPSAL', len(PresT))

        ncvar=ncOUT.createVariable("REFERENCE_DATE_TIME", 'c', ("DATETIME",))
        ncvar[:]=p.time.strftime("%Y%m%d%H%M%S")
        ncvar=ncOUT.createVariable("JULD", 'd', ("NPROF",))
        ncvar[:]=0.0
        ncvar=ncOUT.createVariable("LONGITUDE", "d", ("NPROF",))
        ncvar[:] = p.lon.astype(np.float64)
        ncvar=ncOUT.createVariable("LATITUDE", "d", ("NPROF",))
        ncvar[:] = p.lat.astype(np.float64)


 
        ncvar=ncOUT.createVariable('TEMP','f',('nTEMP',))
        ncvar[:]=Temp
        setattr(ncvar, 'variable'   , 'TEMP')
        setattr(ncvar, 'units'      , "degree_Celsius")
        ncvar=ncOUT.createVariable('PRES_TEMP','f',('nTEMP',))
        ncvar[:]=PresT
        ncvar=ncOUT.createVariable('TEMP_QC','f',('nTEMP',))
        ncvar[:]=QcT

        ncvar=ncOUT.createVariable('PSAL','f',('nTEMP',))
        ncvar[:]=Sali
        setattr(ncvar, 'variable'   , 'SALI')
        setattr(ncvar, 'units'      , "PSS78")
        ncvar=ncOUT.createVariable('PRES_PSAL','f',('nTEMP',))
        ncvar[:]=PresT
        ncvar=ncOUT.createVariable('PSAL_QC','f',('nTEMP',))
        ncvar[:]=QcS

    print("dumping par on " + outfile, flush=True)
    par_already_existing="nPAR" in ncOUT.dimensions.keys()
    if not par_already_existing : ncOUT.createDimension('nDOWNWELLING_PAR', nP)
    ncvar=ncOUT.createVariable("PRES_DOWNWELLING_PAR", 'f', ('nDOWNWELLING_PAR',))
    ncvar[:]=Pres
    ncvar=ncOUT.createVariable("DOWNWELLING_PAR", 'f', ('nDOWNWELLING_PAR',))
    ncvar[:]=Value
    setattr(ncvar, 'status_var' , metadata.status_var)
    setattr(ncvar, 'variable'   , 'DOWNWELLING_PAR')
    setattr(ncvar, 'units'      , "microMoleQuanta/m^2/sec")
    setattr(ncvar, 'longname'   , 'Downwelling photosynthetic available radiation')
    ncvar=ncOUT.createVariable("DOWNWELLING_PAR_QC", 'f', ('nDOWNWELLING_PAR',))
    ncvar[:]=Qc
    ncOUT.close()

    os.system("mv " + outfile + ".tmp " + outfile)

def get_outfile(p,outdir):
    wmo=p._my_float.wmo
    filename="%s%s/%s" %(outdir,wmo, os.path.basename(p._my_float.filename))
    return filename


def par_algorithm(pCor, outfile, metadata,writing_mode):
    Pres, _, _ = pCor.read('TEMP', read_adjusted=False)
    if len(Pres)<5:
        print("few values in Coriolis TEMP in " + pCor._my_float.filename, flush=True)
        log_to_csv(filename, "len_pres_temp_less_5", discarded_file)
        return
    os.system('mkdir -p ' + os.path.dirname(outfile))

    EMPTY_VAR_CHECK=check_bgcvar_empty(outfile,'DOWNWELLING_PAR')
    if EMPTY_VAR_CHECK :
        log_to_csv(filename, "var_is_empty", discarded_file)
        return None, None, None, metadata
    else:
        metadata.status_var = pCor._my_float.status_var('DOWNWELLING_PAR')
        if metadata.status_var in ['A', 'D']:
            Pres, Value, Qc = pCor.read('DOWNWELLING_PAR', read_adjusted=True)
        else:
            Pres, Value, Qc = pCor.read('DOWNWELLING_PAR', read_adjusted=False)
        if Pres is None: 
            log_to_csv(filename, "pres_none", discarded_file)
            return
        if len(Pres)<5:
            print("few values in Coriolis for PAR in " + pCor._my_float.filename, flush=True)
            log_to_csv(filename, "len_pres_par_less_5", discarded_file)
            return
        dump_par_file(outfile, pCor, Pres, Value, Qc, metadata,mode=writing_mode)

OUTDIR = addsep(args.outdir)
input_file=args.update_file
INDEX_FILE=superfloat_generator.read_float_read_float_index(input_file)
nFiles=INDEX_FILE.size
discarded_file = "discarded_DOWNWELLING_PAR.csv" # file that will ist all files disvcarded and motivation

def log_to_csv(file_name, motivation_text, discarded_file):
    """
    write a df file with discarded files nc and their  motivation
    name file in input of script discarded_file = "discarded_DOWNWELLING_PAR.csv"
    Parameters:
        file_name (str): The name of the file to log.
        motivation_text (str): The reason or motivation to log.
        csv_file (str): The name of the CSV file to update or create.
    """
    df = pd.DataFrame({"file_name": [file_name], "motivation": [motivation_text]})
    if os.path.exists(discarded_file):
        df.to_csv(discarded_file, mode="a", header=False, index=False)
    else:
        df.to_csv(discarded_file, index=False)

import pandas as pd
import sys
for iFile in range(nFiles):
    timestr          = INDEX_FILE['date'][iFile].decode()
    lon              = INDEX_FILE['longitude' ][iFile]
    lat              = INDEX_FILE['latitude' ][iFile]
    filename         = INDEX_FILE['file_name'][iFile].decode()
    available_params = INDEX_FILE['parameters'][iFile].decode()
    parameterdatamode= INDEX_FILE['parameter_data_mode'][iFile].decode()
    #float_time = datetime.datetime.strptime(timestr,'%Y%m%d%H%M%S')
    float_time = datetime.datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')
    filename=filename.replace('coriolis/','').replace('profiles/','')

    if  'DOWNWELLING_PAR' in available_params:
         pCor=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
         outfile = get_outfile(pCor,OUTDIR)
         writing_mode=superfloat_generator.writing_mode(outfile)
         metadata = Metadata(pCor._my_float.filename)
         f_serv_ca = pCor._my_float.filename
         try:
            print(f_serv_ca) 
            with Dataset(f_serv_ca , mode='r') as nc_file:
                 par_algorithm(pCor, outfile, metadata, writing_mode)
         except:
            log_to_csv(filename, "corrupted_file", discarded_file) 
    else:
         log_to_csv(filename, "No_downwelling_par_in_available_params", discarded_file)

