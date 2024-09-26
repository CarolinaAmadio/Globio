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
    parser.add_argument(   '--outdiag','-O',
                                type = str,
                                required = True,
                                default = "/gpfs/scratch/userexternal/gbolzon0/SUPERFLOAT/",
                                help = 'path for statistics, diagnostics, logs')
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
import scipy.io.netcdf as NC
import numpy as np
import seawater as sw
from datetime import datetime, timedelta
import bitsea.basins.OGS as OGS
from bitsea.instruments.var_conversions import FLOATVARS
#from commons_local import cross_Med_basins, save_report


class Metadata():
    def __init__(self, filename, status_var):
        self.filename = filename
        self.status_var = status_var


def remove_bad_sensors(Profilelist,var):
    '''

    Subsetter, filtering out bad sensors for that var

     Arguments:
      * Profilelist * list of Profile objects
      * var         * string

      Returns:
        a list of Profile Objects
    '''
 
    OUT_N3n = ["6903197","6901767","6901773","6901771"]
    OUT_O2o = ["6901510"]
    OUT_O2o = ["6901766",'6903235','6902902',"6902700"]
    # 0 6901766 has negative values

    if ( var == 'SR_NO3' ):
        return [p for p in Profilelist if p.name() not in OUT_N3n]

    if ( var == 'DOXY' ):
        return [p for p in Profilelist if p.name() not in OUT_O2o]

    return Profilelist

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

def read_doxy(pCor):
    Pres, Value, Qc = pCor.read('DOXY',read_adjusted=True)
    nP=len(Pres)
    if nP<5 :
        print("few values for " + pCor._my_float.filename, flush=True)
        return None, None, None
    ValueCconv=convert_oxygen(pCor, Pres, Value)
    return Pres, ValueCconv, Qc

def treating_coriolis(pCor):
    metadata = Metadata(pCor._my_float.filename, pCor._my_float.status_var('DOXY'))
    metadata.status_var = pCor._my_float.status_var('DOXY')
    # only adjusted and delayed
    if pCor._my_float.status_var('DOXY') in ['A','D'] :    #istanza di BioFloat
        Pres, DOXY, Qc = read_doxy(pCor)
        return Pres, DOXY, Qc, metadata
    else:
        print("R -- not dumped ", pCor._my_float.filename, flush=True)
        return None, None, None, metadata

def doxy_algorithm(p, outfile, metadata,writing_mode):
    '''
    Arguments:
    * p                * profile object
    * Profilelist_hist * List of profile object, provided by load_history()
    * Dataset          * dictionary, provided by load_history()
    '''
    #Pres, Value, Qc  = p.read('DOXY',read_adjusted=False)
    Pres, _, _ = p.read('TEMP', read_adjusted=False)
    if len(Pres)<5 or (Pres is None):
        print("few values in Coriolis TEMP in " + p._my_float.filename, flush=True)
        return
    
    os.system('mkdir -p ' + os.path.dirname(outfile))
    Pres, DOXY, Qc, metadata = treating_coriolis(p)

    if Pres is None: return # no data
    dump_oxygen_file(outfile, p, Pres, DOXY, Qc, metadata,mode=writing_mode)


# start program
#opa_prex "python superfloat_oxygen.py   -o $DATASET -u $UPDATE_FILE -O $DIAG_DIR"
# outdir      =  $ONLINE_REPO/SUPERFLOAT
# update_file =  filtered_Float_Index.txt
#DIAG_DIR=$DATASET/oxy_diag


OUTDIR = addsep(args.outdir)
OUT_META = addsep(args.outdiag)
input_file=args.update_file

#INDEX_FILE=superfloat_generator.read_float_update(input_file)
INDEX_FILE=superfloat_generator.read_float_read_float_index(input_file)
nFiles=INDEX_FILE.size

import sys
for iFile in range(nFiles):
    timestr          = INDEX_FILE['date'][iFile].decode()
    lon              = INDEX_FILE['longitude' ][iFile]
    lat              = INDEX_FILE['latitude' ][iFile]
    filename         = INDEX_FILE['file_name'][iFile].decode()
    available_params = INDEX_FILE['parameters'][iFile].decode()
    parameterdatamode= INDEX_FILE['parameter_data_mode'][iFile].decode()
    #float_time = datetime.strptime(timestr,'%Y%m%d%H%M%S')
    float_time = datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')
    filename=filename.replace('coriolis/','').replace('profiles/','')



    if 'DOXY' in available_params:

        p=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
        outfile = get_outfile(p,OUTDIR)
        writing_mode=superfloat_generator.writing_mode(outfile)
        metadata = Metadata(p._my_float.filename, p._my_float.status_var('DOXY'))
        doxy_algorithm(p, outfile, metadata,writing_mode)

