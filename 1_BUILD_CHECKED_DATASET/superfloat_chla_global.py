import sys
import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Creates superfloat files of chla.
    Reads from Coriolis dataset.
    It has to be called as the first one of the series of superfloat generators.
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--datestart','-s',
                                type = str,
                                required = False,
                                default = 'NO_data',
                                help = '''date in yyyymmss format''')
    parser.add_argument(   '--dateend','-e',
                                type = str,
                                required = False,
                                default = 'NO_data',
                                help = '''date in yyyymmss format''')
    parser.add_argument(   '--outdir','-o',
                                type = str,
                                required = True,                                
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
from bitsea.basins.region import Rectangle
import superfloat_generator
from bitsea.commons.utils import addsep
import os
import scipy.io as NC
import numpy as np
import datetime

class Metadata():
    def __init__(self, filename):
        self.filename = filename
        self.status_var = 'n'

def get_outfile(p,outdir):
    wmo=p._my_float.wmo
    filename="%s%s/%s" %(outdir,wmo, os.path.basename(p._my_float.filename))
    return filename

def dumpfile(outfile, p,Pres,chl_profile,Qc,metadata):
    PresT, Temp, QcT = p.read('TEMP', read_adjusted=False)
    PresT, Sali, QcS = p.read('PSAL', read_adjusted=False)
    
    print("dumping chla on " + outfile + p.time.strftime(" %Y%m%d-%H:%M:%S"), flush=True)
    ncOUT = NC.netcdf_file(outfile,"w")
    setattr(ncOUT, 'origin'     , 'coriolis')
    setattr(ncOUT, 'file_origin', metadata.filename)

    ncOUT.createDimension("DATETIME",14)
    ncOUT.createDimension("NPROF", 1)

    ncOUT.createDimension('nTEMP', len(PresT))
    ncOUT.createDimension('nPSAL', len(PresT))
    ncOUT.createDimension('nCHLA', len(Pres ))    

    ncvar=ncOUT.createVariable("REFERENCE_DATE_TIME", 'c', ("DATETIME",))
    ncvar[:]=p.time.strftime("%Y%m%d%H%M%S")
    ncvar=ncOUT.createVariable("JULD", 'd', ("NPROF",))
    ncvar[:]=0.0
    ncvar=ncOUT.createVariable("LONGITUDE", "d", ("NPROF",))
    ncvar[:] = p.lon.astype(np.float64)
    ncvar=ncOUT.createVariable("LATITUDE", "d", ("NPROF",))
    ncvar[:] = p.lat.astype(np.float64)

    
    ncvar=ncOUT.createVariable('TEMP','f',('nTEMP',))
    ncvar[:] = Temp
    setattr(ncvar, 'variable'   , 'TEMP')
    setattr(ncvar, 'units'      , "degree_Celsius")

    ncvar=ncOUT.createVariable('PRES_TEMP','f',('nTEMP',))
    ncvar[:]=PresT
    ncvar=ncOUT.createVariable('TEMP_QC','f',('nTEMP',))
    ncvar[:]=QcT

    ncvar=ncOUT.createVariable('PSAL','f',('nPSAL',))
    ncvar[:]=Sali
    setattr(ncvar, 'variable'   , 'SALI')
    setattr(ncvar, 'units'      , "PSS78")

    ncvar=ncOUT.createVariable('PRES_PSAL','f',('nPSAL',))
    ncvar[:]=PresT
    ncvar=ncOUT.createVariable('PSAL_QC','f',('nPSAL',))
    ncvar[:]=QcS

    ncvar=ncOUT.createVariable('CHLA','f',('nCHLA',))
    ncvar[:]=chl_profile
    setattr(ncvar, 'status_var' , metadata.status_var)
    setattr(ncvar, 'variable'   , 'CHLA_ADJUSTED')
    setattr(ncvar, 'units'      , "milligram/m3")

    ncvar=ncOUT.createVariable('PRES_CHLA','f',('nCHLA',))
    ncvar[:]=Pres
    ncvar=ncOUT.createVariable('CHLA_QC','f',('nCHLA',))
    ncvar[:]=Qc
    ncOUT.close()

def treating_coriolis(pCor):
    metadata = Metadata(pCor._my_float.filename)
    metadata.status_var = pCor._my_float.status_var('CHLA')
    # only adjusted and delayed
    if pCor._my_float.status_var('CHLA') in ['A','D'] :    #istanza di BioFloat
        Pres,CHL, Qc=pCor.read('CHLA', read_adjusted=True) #pCor istanza  do BioFloatProfile
        if len(Pres)<5:
            print("few values in Coriolis in CHLA for " + pCor._my_float.filename, flush=True)
            return None, None, None, metadata

        return Pres, CHL, Qc, metadata
    else:
        print("R -- not dumped ", pCor._my_float.filename, flush=True)
        return None, None, None, metadata

def chla_algorithm(pCor,outfile):
    Pres, _, _ = pCor.read('TEMP', read_adjusted=False)
    if len(Pres)<5:
        print("few values in Coriolis TEMP in " + pCor._my_float.filename, flush=True)
        return
    os.system('mkdir -p ' + os.path.dirname(outfile))

    Pres, CHL, Qc, metadata = treating_coriolis(pCor)

    if Pres is None: return # no data
    dumpfile(outfile, pCor, Pres, CHL, Qc, metadata)


# start program 
# opa_prex "python superfloat_chla.py     -o $DATASET -u $UPDATE_FILE"
# outdir      =  $ONLINE_REPO/SUPERFLOAT
# update_file =  filtered_Float_Index.txt

OUTDIR = addsep(args.outdir)
input_file=args.update_file

#INDEX_FILE=superfloat_generator.read_float_update(input_file) # legge il file dando i caratteri int float etc

INDEX_FILE=superfloat_generator.read_float_read_float_index(input_file)


nFiles=INDEX_FILE.size 

#print(INDEX_FILE)

import sys 

for iFile in range(nFiles): # loop su tuttie le righe del float index 
    timestr          = INDEX_FILE['date'][iFile].decode()
    lon              = INDEX_FILE['longitude' ][iFile]
    lat              = INDEX_FILE['latitude' ][iFile]
    filename         = INDEX_FILE['file_name'][iFile].decode()
    available_params = INDEX_FILE['parameters'][iFile].decode()
    parameterdatamode= INDEX_FILE['parameter_data_mode'][iFile].decode()
    #float_time = datetime.datetime.strptime(timestr,'%Y%m%d%H%M%S')
    float_time = datetime.datetime.strptime(timestr, '%Y%m%d-%H:%M:%S')
    filename=filename.replace('coriolis/','').replace('profiles/','')
       
    if 'CHLA' in available_params:
        pCor=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
        # profile_gen: (1) Crea un'istanza di BioFloat (2) Crea un'istanza di BioFloatProfile ma nn
        # ho correzioni (non ho ancora chiamato la pread
        outfile = get_outfile(pCor, OUTDIR) # mi rida il nome del file
        chla_algorithm(pCor, outfile)

