from commons.utils import addsep
import sys
sys.path.append("/g100/home/userexternal/camadio0/CA_functions/")
import pandas as pd
import numpy as np
from funzioni_CA import parsing_path, new_directory, globe_Map
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import warnings
warnings.filterwarnings('ignore')
import os
from bitsea.instruments.var_conversions import FLOATVARS

INPUTDIR = "/g100_work/OGS_devC/camadio/GLOBIO/SEANOE_SAUZ/SFILES_FINAL_v2/Globio_branch_SEANOE/2_DATASET_ANALYSIS/"
INDEXTXT = '20000101_20241110_'
varlist = ['P_l', 'O2o','N3n', 'PAR','POC','pH']

os.makedirs("FIGURES", exist_ok=True)

markers = ['o', 'o', 's','.','.','.']
colors = ['#0072B2', '#E69F00', '#009E73']  #
colors = ['blue', 'mediumaquamarine', 'w']  #
colors = ['w','red', 'cyan','k','k','k','gold','gray','dodgerblue','orange']
dim = [100,30,20,15,15,15]
edge= ['k','k','k','k','k','k']
alph=[1,1,0.3,0.2,0.2,0.2]
# Creazione della figura e della mappa
fig, ax = plt.subplots(figsize=(15, 8))
plt.grid(color='grey', linestyle='--', linewidth=0.5, alpha=0.5)

map = Basemap(projection='cyl', llcrnrlat=-80, urcrnrlat=80,
              llcrnrlon=-180, urcrnrlon=180, resolution='l', ax=ax)
map.drawcoastlines(color='black', linewidth=0.7)
map.fillcontinents(color='#f5f5dc', lake_color='#d1ecf1')
map.drawmapboundary(fill_color='#d1ecf1')
map.drawparallels(np.arange(-60, 61, 20), labels=[True, False, False, False], color='gray', alpha=0.5)
map.drawmeridians(np.arange(-180, 181, 30), labels=[False, False, False, True], color='gray', alpha=0.5)

handles = []  # Lista per gestire la legenda


# Loop per plottare le variabili
for i, VAR in enumerate(varlist):
    #vv = VARLIST[i]
    vv = FLOATVARS[VAR]
    df_multi_year = pd.read_csv(INPUTDIR + INDEXTXT + VAR + '__' + vv + '.csv', index_col=0)
    df_multi_year = df_multi_year.groupby('name')[['lat', 'lon']].mean().reset_index()

    lat_multi_year = np.array(df_multi_year.lat)
    lon_multi_year = np.array(df_multi_year.lon)
    lons_multi_year, lats_multi_year = map(lon_multi_year, lat_multi_year)

    # Plot dei punti per ciascuna variabile
    #plt.scatter(lons_multi_year, lats_multi_year, marker=markers[i] , edgecolors='k',
    #            s=dim[i], color=colors[i], alpha=0.7)
    
    scatter = plt.scatter(lons_multi_year, lats_multi_year, marker=markers[i], edgecolors=edge[i] ,
                s=dim[i], color=colors[i], alpha=0.7, label=vv)
    handles.append(scatter)
    map.fillcontinents(color='#f5f5dc', lake_color='#d1ecf1')
# Titolo
plt.title('Position of Floats - Multi-variable Map', fontsize=16, color='darkblue', weight='bold', style='italic')
ax.legend(handles=handles, title="Variables", loc='upper center', bbox_to_anchor=(0.5, -0.04), fontsize=12, title_fontsize=16, ncol=6, frameon=False)

# Salvataggio del grafico
plt.tight_layout()
plt.savefig('FIGURES/multi_variable_map_21.png', dpi=300)
plt.close(fig)

