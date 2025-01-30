import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--datestart','-s',
                                type = str,
                                required = False,
                                help = '''date in yyyymmdd format''')
    parser.add_argument(   '--dateend','-e',
                                type = str,
                                required = False,
                                help = '''date in yyyymmdd format ''')
    parser.add_argument(   '--var','-v',
                                type = str,
                                required = False,
                                default = 'NO_file',
                                help = '''file with updated floats''')
    return parser.parse_args()

args = argument()

import logging

LOGGER = logging.getLogger()


def configure_logger():
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    LOGGER.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

configure_logger()

LOGGER.debug('parto')

import numpy as np
import pandas as pd
from bitsea.commons.time_interval import TimeInterval
from bitsea.commons.Timelist import TimeList
import bitsea.basins.OGS as OGS
LOGGER.debug('step 0')
from bitsea.instruments import seanoe
from bitsea.instruments.var_conversions import FLOATVARS
from bitsea.commons.utils import addsep
from datetime import timedelta
from datetime import datetime
LOGGER.debug('step 1')
from bitsea.commons import timerequestors
import numpy as np
import sys
sys.path.append("/g100/home/userexternal/camadio0/CA_functions/")
import funzioni_CA
from basins_CA_new_bitsea import identify_ocean_basin
LOGGER.debug("start program")

DATE_start  = args.datestart
DATE_end    = args.dateend
varmod      = args.var

LISTVAR=['O2o','N3n','P_l','P_i','Chla','vosaline','votemper','PAR','POC','P_c','BBP532','pH']
if varmod in LISTVAR:
    VARNAME =FLOATVARS[varmod]
else:
   VARNAME=varmod

LOGGER.debug("start program1")
endstr  = '/'
TSS= DATE_start+'_'+DATE_end+'_'+varmod+'_'  # string used in savefig and savecsv
TI_3  = timerequestors.TimeInterval(starttime=DATE_start, endtime=DATE_end, dateformat='%Y%m%d')

LOGGER.debug("start program2")
Profilelist=seanoe.FloatSelector(FLOATVARS[varmod],TI_3, OGS.world)
LOGGER.debug ('...              Date start  ' + DATE_start)
LOGGER.debug ('...              Date end  ' + DATE_end)
LOGGER.debug ('...              len Profilelist  ' + str(len(Profilelist)))
LOGGER.debug ('...              Name of var  ' + VARNAME)
LOGGER.debug('....              in the world')

import sys
sys.exit()

#__Profilelist=superfloat.FloatSelector(None,TI_3, OGS.world)
#print ('...              len Profilelist no vars ' + str(len(__Profilelist)))
#del (__Profilelist )

df= pd.DataFrame(index=np.arange(0,len(Profilelist)), columns=['ID','time','lat','lon','name','cycle','Type','qc','basin'])
from bitsea.instruments.var_conversions import FLOATVARS
for iii in range(0,len(Profilelist)):
    df.ID[iii]   = Profilelist[iii]._my_float.filename
    df.time[iii] = Profilelist[iii].time
    df.lat[iii]  = Profilelist[iii].lat
    df.lon[iii]  = Profilelist[iii].lon
    df.name[iii] = Profilelist[iii].name()
    df.cycle[iii] = Profilelist[iii]._my_float.cycle
    if varmod=='votemper':
        TYPE_TMP = np.nan
    else:
        TYPE_TMP     = Profilelist[iii]._my_float.origin(VARNAME)
        TYPE_TMP     = TYPE_TMP.status_var
    df.Type[iii] = TYPE_TMP
    p=Profilelist[iii]
    Pres, Profile, Qc = p.read(FLOATVARS[varmod])
    df.qc[iii]        = (np.unique(Qc))
    NAME_BASIN, BORDER_BASIN = identify_ocean_basin(Profilelist[iii].lat , Profilelist[iii].lon )
    df.basin.iloc[iii] = NAME_BASIN
    # Print ogni 10.000 iterazioni
    if (iii + 1) % 10000 == 0:
        print(f"Processed {iii + 1} profiles")


# mpnths columns 
df['time'] =  pd.to_datetime(df['time']) #deprecated infer_datetime_format=True)
df['date']=df.time.dt.date
df['n_profiles_per_day']=1
df.date =pd.to_datetime(df.date)
df['month'] = df.date.dt.month
df['year'] = df.date.dt.year
df = df.sort_values(by='date',ascending=True)
df.index=np.arange(0,len(df))


df.to_csv(TSS+'_'+VARNAME+'.csv' )
