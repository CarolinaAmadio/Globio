from datetime import datetime
from argopy import DataFetcher
import gsw
import xarray as xr

start_date = datetime(2020, 7, 1).strftime("%Y-%m-%d")
end_date = datetime(2020, 7, 30).strftime("%Y-%m-%d")
region = [-5, 36, 30, 46, 0, 2000, start_date, end_date]
params = ['DOXY', 'TEMP', 'PSAL']
ds = DataFetcher(mode='standard', ds='bgc', params=params).region(region).to_xarray()

profiles = ds.argo.point2profile()
mask = ((profiles['PLATFORM_NUMBER'] == 6901774) & (profiles['CYCLE_NUMBER'] == 116))

p = profiles.where(mask, drop=True).squeeze()

# remove nan 
valid = p['PRES'].notnull() & p['DOXY'].notnull()
p_pres = p['PRES'].where(valid, drop=True)
p_doxy = p['DOXY'].where(valid, drop=True)

# varconversion with gsw n
SA = gsw.SA_from_SP(p["PSAL"].values, p["PRES"].values, p["LONGITUDE"].values, p["LATITUDE"].values)
CT = gsw.CT_from_t(SA ,p["TEMP"].values, p["PRES"].values)
density = gsw.rho(SA, CT, p["PRES"].values)
# µmol/kg ---> mmol/m3
p_doxy = p['DOXY'] * density / 1000.0
p_pres = p['PRES']

#superfloat static dataaset
inputfile= "/g100_scratch/usera07ogs/a07ogs00/V12C/ONLINE/SUPERFLOAT/6901774/SD6901774_116.nc"
ds_sf = xr.open_dataset(inputfile)
s_oxy = ds_sf["DOXY"]
s_pres = ds_sf["PRES_DOXY"]


# plot fig
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 8))
ax.plot(p_doxy, p_pres, color='tab:orange', label='ARGOPY')
ax.plot(s_oxy, s_pres, color='dodgerblue', label='SUPERFLOAT')
ax.invert_yaxis()
ax.set_xlabel(r'DOXY (mmol m$^{-3}$)')
ax.set_ylabel('Pressure (dbar)')
ax.set_title('Oxygen profile comparison')
ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()
fig.savefig('DOXY_profile_comparison.png')


print(ds)
print(ds.attrs)
print(profiles.attrs)
print(profiles['PRES'].isel(N_PROF=0).values)
