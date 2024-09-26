import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Creates superfloat files of PH_IN_SITU_TOTAL.
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
from bitsea.basins.region import Rectangle
import superfloat_generator
from bitsea.commons.utils import addsep
import os
import scipy.io.netcdf as NC
import numpy as np
import datetime

class Metadata():
    def __init__(self, filename):
        self.filename = filename
        self.status_var = 'n'

def dump_ph_file(outfile, p, Pres, Value, Qc, metadata, mode='w'):
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

    print("dumping ph on " + outfile, flush=True)
    ph_already_existing="nPH_IN_SITU_TOTAL" in ncOUT.dimensions.keys()
    if not ph_already_existing : ncOUT.createDimension('nPH_IN_SITU_TOTAL', nP)
    ncvar=ncOUT.createVariable("PRES_PH_IN_SITU_TOTAL", 'f', ('nPH_IN_SITU_TOTAL',))
    ncvar[:]=Pres
    ncvar=ncOUT.createVariable("PH_IN_SITU_TOTAL", 'f', ('nPH_IN_SITU_TOTAL',))
    ncvar[:]=Value
    setattr(ncvar, 'status_var' , metadata.status_var)
    setattr(ncvar, 'variable'   , 'PH_IN_SITU_TOTAL')
    setattr(ncvar, 'units'      , "dimensionless")
    setattr(ncvar, 'longname'   , 'sea_water_ph_reported_on_total_scale')
    ncvar=ncOUT.createVariable("PH_IN_SITU_TOTAL_QC", 'f', ('nPH_IN_SITU_TOTAL',))
    ncvar[:]=Qc
    ncOUT.close()

    os.system("mv " + outfile + ".tmp " + outfile)

def get_outfile(p,outdir):
    wmo=p._my_float.wmo
    filename="%s%s/%s" %(outdir,wmo, os.path.basename(p._my_float.filename))
    return filename

def ph_algorithm(pCor, outfile, metadata,writing_mode):
    Pres, _, _ = pCor.read('TEMP', read_adjusted=False)
    if len(Pres)<5:
        print("few values in Coriolis TEMP in " + pCor._my_float.filename, flush=True)
        return
    os.system('mkdir -p ' + os.path.dirname(outfile))
    metadata.status_var = pCor._my_float.status_var('PH_IN_SITU_TOTAL')
    if metadata.status_var in ['A', 'D']:
        Pres, Value, Qc = pCor.read('PH_IN_SITU_TOTAL', read_adjusted=True)
    else:
        Pres, Value, Qc = pCor.read('PH_IN_SITU_TOTAL', read_adjusted=False)
    if Pres is None: return
    if len(Pres)<5:
        print("few values in Coriolis for pH in " + pCor._my_float.filename, flush=True)
        return
    dump_ph_file(outfile, pCor, Pres, Value, Qc, metadata,mode=writing_mode)


input_file=args.update_file
OUTDIR = addsep(args.outdir)
INDEX_FILE=superfloat_generator.read_float_read_float_index(input_file)
nFiles=INDEX_FILE.size

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

    if  'PH_IN_SITU_TOTAL' in available_params:
         pCor=bio_float.profile_gen(lon, lat, float_time, filename, available_params,parameterdatamode)
         outfile = get_outfile(pCor,OUTDIR)
         writing_mode=superfloat_generator.writing_mode(outfile)

         metadata = Metadata(pCor._my_float.filename)
         ph_algorithm(pCor, outfile, metadata, writing_mode)
