import argparse
from pathlib import Path

def argument():
    parser = argparse.ArgumentParser(
        description='''
    Downloads BGC-Argo profiles using argopy for a predefined region
    and time period, and exports each profile to an individual NetCDF file.

    The script retrieves DOXY, TEMP and PSAL data in standard mode
    (as defined by argopy) and converts dissolved oxygen from µmol/kg
    to mmol/m3 using TEOS-10 seawater density calculations.

    Output: one NetCDF file per profile.
    ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--outdir', '-o',type=str,required=True,help='Output directory for the generated NetCDF profile files.')

    return parser.parse_args()

args = argument()

import numpy as np
from datetime import datetime
from argopy import DataFetcher
import xarray as xr
import netCDF4 as NC
import gsw

params = ['DOXY', 'TEMP', 'PSAL']
outdir = Path(args.outdir)
outdir.mkdir(parents=True, exist_ok=True)

start_date = datetime(2020, 7, 1).strftime("%Y-%m-%d")
end_date = datetime(2020, 7, 30).strftime("%Y-%m-%d")
region = [-5, 36, 30, 46, 0, 2000, start_date, end_date]
params = ['DOXY', 'TEMP', 'PSAL']
ds = DataFetcher(mode='standard', ds='bgc', params=params).region(region).to_xarray()
profiles = ds.argo.point2profile()


def get_values(p, var):
    """ read vars, qc and filter nan"""
    pres = p['PRES'].values
    values = p[var].values
    valid = np.isfinite(pres) & np.isfinite(values)
    qc_name = f'{var}_QC'
    if qc_name in p:
        qc = p[qc_name].values
    else:
        import sys 
        sys.exit("not yet implemented") # ma nn dovrebbe mai entrare qui

    # If QC is scalar (e.g. TEMP_QC, PSAL_QC), repeat it
    # for all pressure levels
    if np.ndim(qc) == 0 and var != 'DOXY':
        qc = np.full(values.shape, qc)
    else:
        qc = np.asarray(qc)
    
    return pres[valid], values[valid], qc[valid]
    return pres[valid], values[valid], qc[valid]

for i in range(profiles.sizes['N_PROF']):
    print(i)
    p = profiles.isel(N_PROF=i)
    # Metadata to dump
    time = np.datetime_as_string(p['TIME'].values, unit='s')
    time = time.replace('-', '').replace(':', '').replace('T', '')
    lat = float(p['LATITUDE'].values)
    lon = float(p['LONGITUDE'].values)
    wmo = str(p['PLATFORM_NUMBER'].values)
    cycle = int(p['CYCLE_NUMBER'].values)

    outdir_wmo = outdir / wmo
    outdir_wmo.mkdir(parents=True, exist_ok=True)
    outfile = outdir_wmo / f'{wmo}_{cycle:03d}.nc'

    # Extract TEMP e PSAL w/o NaN
    PresT, Temp, QcT = get_values(p, 'TEMP')
    PresS, Sali, QcS = get_values(p, 'PSAL')
    # vars to dump in a netcdf
    pres = p['PRES'].values
    doxy = p['DOXY'].values
    temp = p['TEMP'].values
    psal = p['PSAL'].values
    valid = (np.isfinite(pres) & np.isfinite(doxy) & np.isfinite(temp) & np.isfinite(psal))

    PresD = pres[valid]
    Doxy = doxy[valid]
    TempD = temp[valid]
    SaliD = psal[valid]
    QcD = (
        p['DOXY_QC'].values[valid]
        if 'DOXY_QC' in p
        else np.full(valid.sum(), 9, dtype='i1'))

    # Conversion DOXY: µmol/kg -> mmol/m3
    SA = gsw.SA_from_SP(SaliD, PresD, lon, lat)
    CT = gsw.CT_from_t(SA, TempD, PresD)
    density = gsw.rho(SA, CT, PresD)

    Doxy = Doxy * density / 1000.0

    # Dumping netcdf
    with NC.Dataset(outfile, 'w') as ncOUT:

        ncOUT.origin = 'coriolis'
        ncOUT.createDimension('DATETIME', 14)
        ncOUT.createDimension('NPROF', 1)
        ncOUT.createDimension('nTEMP', len(Temp))
        ncOUT.createDimension('nPSAL', len(Sali))
        ncOUT.createDimension('nDOXY', len(Doxy))

        def write_var(name, dtype, dims, values, **attrs):
            var = ncOUT.createVariable(name, dtype, dims)
            var[:] = values
            for key, value in attrs.items():
                setattr(var, key, value)
            return var

        write_var(
            'REFERENCE_DATE_TIME', 'S1', ('DATETIME',),
            np.array(list(time), dtype='S1'))

        write_var('JULD', 'd', ('NPROF',), [0.0])
        write_var('LONGITUDE', 'd', ('NPROF',), [lon])
        write_var('LATITUDE', 'd', ('NPROF',), [lat])
        # TEMP
        write_var('TEMP', 'f4', ('nTEMP',), Temp, variable='TEMP', units='degree_Celsius')
        write_var('PRES_TEMP', 'f4', ('nTEMP',), PresT)
        write_var('TEMP_QC', 'S1', ('nTEMP',), QcT.astype('S1'))

        # PSAL
        write_var('PSAL', 'f4', ('nPSAL',), Sali,variable='SALI', units='PSS78')
        write_var('PRES_PSAL', 'f4', ('nPSAL',), PresS)
        write_var('PSAL_QC', 'S1', ('nPSAL',), QcS.astype('S1'))

        # DOXY 
        write_var('DOXY', 'f4', ('nDOXY',), Doxy,variable='DOXY', units='mmol/m3')
        write_var('PRES_DOXY', 'f4', ('nDOXY',), PresD)
        write_var('DOXY_QC', 'S1', ('nDOXY',), QcD.astype('S1'))

