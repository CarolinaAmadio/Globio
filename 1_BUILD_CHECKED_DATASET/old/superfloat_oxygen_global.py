import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Creates superfloat files of dissolved oxygen.
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


import pandas as pd
from bitsea.instruments import bio_float
from bitsea.Float import oxygen_saturation
from bitsea.commons.time_interval import TimeInterval
from bitsea.basins.region import Rectangle
import superfloat_generator
from bitsea.commons.utils import addsep
import os
from scipy.io.netcdf import netcdf_file
import numpy as np
import seawater as sw
from datetime import datetime, timedelta
import bitsea.basins.OGS as OGS
from bitsea.instruments.var_conversions import FLOATVARS
from netCDF4 import Dataset
#from commons_local import cross_Med_basins, save_report


class Metadata():
    def __init__(self, filename, status_var):
        self.filename = filename
        self.status_var = status_var

def check_units_doxy2(p,outfile):
    coriolis_file=outfile.replace('_QCed','')
    #coriolis_file=outfile.replace('SUPERFLOAT','CORIOLIS')
    nc = Dataset(coriolis_file)
    doxy_var = nc.variables['DOXY2']
    doxy_units = doxy_var.units
    if doxy_units == 'micromole/kg': return True
    else: return False

def convert_oxygen(p,doxypres,doxyprofile):
    '''
    from micromol/Kg to  mmol/m3
    '''
    if doxypres.size == 0: return doxyprofile
    Pres, temp, Qc = p.read("TEMP",read_adjusted=False)
    Pres, sali, Qc = p.read("PSAL",read_adjusted=False)
    density = sw.dens(sali,temp,Pres)
    density_on_zdoxy = np.interp(doxypres,Pres,density)
    return doxyprofile * density_on_zdoxy/1000.

def dump_oxygen_file(outfile, p, Pres, Value, Qc, metadata, mode='w'):
    nP=len(Pres)
    if mode=='a':
        command = "cp %s %s.tmp" %(outfile,outfile)
        os.system(command)
    ncOUT = netcdf_file(outfile + ".tmp", mode)


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

    print("dumping oxygen on " + outfile, flush=True)
    doxy_already_existing="nDOXY" in ncOUT.dimensions.keys()
    if not doxy_already_existing : ncOUT.createDimension('nDOXY', nP)
    ncvar=ncOUT.createVariable("PRES_DOXY", 'f', ('nDOXY',))
    ncvar[:]=Pres
    ncvar=ncOUT.createVariable("DOXY", 'f', ('nDOXY',))
    ncvar[:]=Value
    #if not doxy_already_existing:
    setattr(ncvar, 'status_var' , metadata.status_var)
    #setattr(ncvar, 'drift_code' , metadata.drift_code)
    #setattr(ncvar, 'offset'     , metadata.offset)
    setattr(ncvar, 'variable'   , 'DOXY')
    setattr(ncvar, 'units'      , "mmol/m3")
    ncvar=ncOUT.createVariable("DOXY_QC", 'f', ('nDOXY',))
    ncvar[:]=Qc
    ncOUT.close()

    os.system("mv " + outfile + ".tmp " + outfile)


def get_outfile(p,outdir):
    wmo=p._my_float.wmo
    filename="%s%s/%s" %(outdir,wmo, os.path.basename(p._my_float.filename))
    return filename

def check_bgcvar_empty(outfile,VARNAME='DOXY' ):
    #coriolis_file=outfile.replace('SUPERFLOAT','CORIOLIS')
    coriolis_file=outfile.replace('_QCed','')
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

def read_doxy(pCor):
    Pres, Value, Qc = pCor.read('DOXY',read_adjusted=True)
    nP=len(Pres)
    if nP<5 :
        print("few values for " + pCor._my_float.filename, flush=True)
        return None, None, None
    ValueCconv=convert_oxygen(pCor, Pres, Value)
    return Pres, ValueCconv, Qc

def treating_coriolis(pCor, outfile=None):
    if 'DOXY' in available_params.rsplit(" "):
        NAMEVAR='DOXY'
    elif 'DOXY2' in available_params.rsplit(" "):
        NAMEVAR='DOXY2'
    else:
        print(pCor._my_float.filename + 'doesnt have doxy params: ')
        print( available_params.rsplit(" "))
        log_to_csv(filename, "no_doxy_params", discarded_file)
        raise ValueError("no doxy in the profile")

    metadata = Metadata(pCor._my_float.filename, pCor._my_float.status_var(NAMEVAR))
    metadata.status_var = pCor._my_float.status_var(NAMEVAR)
    # only adjusted and delayed
    if pCor._my_float.status_var(NAMEVAR) in ['A','D'] :    #istanza di BioFloat
        if not outfile: # non do la stringa di outfile come  in bitsea originale
           Pres, DOXY, Qc = read_doxy(pCor)
           return Pres, DOXY, Qc, metadata
        else:
           #coriolis_file=outfile.replace('SUPERFLOAT','CORIOLIS')
           coriolis_file=outfile.replace('_QCed','')
           nc = Dataset(coriolis_file)
           EMPTY_VAR_CHECK=check_bgcvar_empty(outfile, NAMEVAR )
           if EMPTY_VAR_CHECK :
               log_to_csv(filename, "var_is_empty", discarded_file)
               return None, None, None, metadata
           else:
               Pres, DOXY , Qc=pCor.read('DOXY', read_adjusted=True)
               return Pres, DOXY, Qc, metadata

    else:
       print("R -- not dumped ", pCor._my_float.filename, flush=True)
       log_to_csv(filename, "RT_doxy_not_used ", discarded_file)
       return None, None, None, metadata

def doxy_algorithm(p, outfile, metadata,writing_mode):
    '''
    Arguments:
    * p                * profile object
    * Profilelist_hist * List of profile object, provided by load_history()
    * Dataset          * dictionary, provided by load_history()
    '''
    Pres, _, _ = p.read('TEMP', read_adjusted=False)
    if len(Pres)<5 or (Pres is None):
        print("few values in Coriolis TEMP in " + p._my_float.filename, flush=True)
        log_to_csv(filename, "len_pres_temp_less_5", discarded_file)
        return
    
    os.system('mkdir -p ' + os.path.dirname(outfile))
    if CHECK_EMPTY_VALUES:
        Pres, DOXY, Qc, metadata = treating_coriolis(p, outfile)
    else:    
        Pres, DOXY, Qc, metadata = treating_coriolis(p)
    if Pres is None: 
        log_to_csv(filename, "pres_none", discarded_file)
        return # no data
    dump_oxygen_file(outfile, p, Pres, DOXY, Qc, metadata,mode=writing_mode )

OUTDIR = addsep(args.outdir)
input_file=args.update_file
CHECK_EMPTY_VALUES=True
INDEX_FILE=superfloat_generator.read_float_read_float_index(input_file)
nFiles=INDEX_FILE.size
discarded_file = "discarded_DOXY.csv" # file that will ist all files disvcarded and motivation

import sys
#sys.exit('exit carol')

def log_to_csv(file_name, motivation_text, discarded_file):
    """
    write a df file with discarded files nc and their  motivation
    name file in input of script discarded_file = "discarded_CHLA.csv"
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
#for iFile in range(0,300):    
    timestr          = INDEX_FILE['date'][iFile].decode()
    lon              = INDEX_FILE['longitude' ][iFile]
    lat              = INDEX_FILE['latitude' ][iFile]
    filename         = INDEX_FILE['file_name'][iFile].decode()
    available_params = INDEX_FILE['parameters'][iFile].decode()
    parameterdatamode= INDEX_FILE['parameter_data_mode'][iFile].decode()
    #float_time = datetime.strptime(timestr,'%Y%m%d%H%M%S')
    float_time = datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')
    filename=filename.replace('coriolis/','').replace('profiles/','')

    if 'DOXY' in available_params.rsplit(" "):
        p=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
        #p = pCor
        outfile = get_outfile(p,OUTDIR)
        writing_mode=superfloat_generator.writing_mode(outfile)
        metadata = Metadata(p._my_float.filename, p._my_float.status_var('DOXY'))
        f_serv_ca = p._my_float.filename
        try:
            with Dataset(f_serv_ca , mode='r', format="NETCDF4") as nc_file:
                doxy_algorithm(p, outfile, metadata,writing_mode)
        except:
            log_to_csv(filename, "corrupted_file", discarded_file)
    elif 'DOXY2' in available_params.rsplit(" "):
        p=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
        #p = pCor
        f_serv_ca = p._my_float.filename
        outfile = get_outfile(p,OUTDIR)
        BOOL= check_units_doxy2(p,outfile)
        if BOOL:
           writing_mode=superfloat_generator.writing_mode(outfile)
           metadata = Metadata(p._my_float.filename, p._my_float.status_var('DOXY2'))
           f_serv_ca = pCor._my_float.filename
           try:
               with Dataset(f_serv_ca , mode='r', format="NETCDF4") as nc_file:
                   doxy_algorithm(p, outfile, metadata,writing_mode)
           except:
               log_to_csv(filename, "corrupted_file", discarded_file)
        else:
           log_to_csv(filename, "units_doxy_no_micromole/kg", discarded_file) 


    else:
        log_to_csv(filename, "No_doxy_in_available_params", discarded_file)

