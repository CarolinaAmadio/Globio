import sys
sys.path.append("/g100/home/userexternal/camadio0/CA_functions/")
import pandas as pd
import numpy as np
from funzioni_CA import globe_Map
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from bitsea.instruments.var_conversions import FLOATVARS
import matplotlib.colors as mcolors


#INPUTDIR = "/g100_work/OGS_devC/camadio/GLOBIO/Globio/2_DATASET_ANALYSIS/"
INPUTDIR = "/g100_work/OGS_devC/camadio/GLOBIO/SEANOE_SAUZ/SFILES_FINAL_v2/Globio_branch_SEANOE/2_DATASET_ANALYSIS/"
INDEXTXT = '20000101_20241110_'
varlist = ['P_l', 'N3n', 'O2o','PAR','POC','pH']
#VARLIST = ['CHLA', 'NITRATE', 'DOXY']

import os
os.makedirs("FIGURES", exist_ok=True)

def ADD_season(df):
    conditions = [
    df['month'].isin([1, 2, 3]),
    df['month'].isin([4, 5, 6]),
    df['month'].isin([7, 8, 9]),
    df['month'].isin([10, 11, 12])]
    seasons = ['winter', 'spring', 'summer', 'autumn']
    df['season'] = np.select(conditions, seasons, default='unknown')
    return df

def Adjust_basin_name(df):
    df["basin"] = df["basin"].replace("Mare Continentale o Indefinito", "Marginal Seas")
    df["basin"] = df["basin"].replace('N. Pacific'   , 'Pacific_North')
    df["basin"] = df["basin"].replace('W. Antartic'  , 'Antartic')
    df["basin"] = df["basin"].replace('S. Atlantic','Atlantic_South' )
    df["basin"] = df["basin"].replace('N. Atlantic','Atlantic_North' )
    df["basin"] = df["basin"].replace('Mediterranean Sea','Mediterranean_Sea' )
    df["basin"] = df["basin"].replace('S. Pacific','Pacific_South' )
    return(df)


colors = ['silver', 'cyan','gold','gray','dodgerblue','orange']
base_colors = list(mcolors.TABLEAU_COLORS.values())  # Colori base di 'tab10'
colors_with_alpha = [(r, g, b, 0.5) for r, g, b in [mcolors.to_rgb(c) for c in base_colors]]

III = 0
for VAR in varlist:
    vv = FLOATVARS[VAR]
    #vv = VARLIST[III]
    df = pd.read_csv(INPUTDIR + INDEXTXT + VAR + '__' + vv + '.csv', index_col=0)
    III+=1
    df["basin"] = df["basin"].replace("Mare Continentale o Indefinito", "Marginal Seas")
    ADD_season(df)
    Adjust_basin_name(df)
    df = df.sort_values(by="basin").reset_index(drop=True)
    df1 = df.groupby(by=['basin','season']).count()
    df1.reset_index(inplace=True)
    df2 = df1[['basin','season','n_profiles_per_day']]
    df_pivot = df2.pivot_table(index="basin", columns="season", values="n_profiles_per_day", fill_value=0)
    ax = df_pivot.plot(kind="bar", stacked=True, figsize=(10, 6), colormap="tab10", alpha=0.5)
    plt.grid(color='grey', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.xlabel("Basin", fontsize=18)
    plt.ylabel("Number of Profiles", fontsize=18)
    plt.title( VAR + " Profiles per Basin and season " , fontsize=18)
    plt.xticks(rotation=45, ha="right", fontsize=18)
    plt.tight_layout()
    df_pivot.to_csv('FIGURES/'+'basin_season_'+VAR+'.csv')
    plt.savefig('FIGURES/basin_season_'+VAR+'.png', dpi=300)
    plt.close()


    df1 = df.groupby('basin', as_index=False)['n_profiles_per_day'].sum()

    plt.figure(figsize=(10, 10))
    plt.pie(
    df1["n_profiles_per_day"],  # Dati
    labels=df1["basin"],  # Etichette
    autopct='%1.1f%%',  # Percentuali
    startangle=90,  # Angolo iniziale
    colors=plt.cm.Pastel1.colors,
    textprops={'fontsize': 18},
    labeldistance=1.1
    )
    plt.tight_layout()
    plt.title("Distribution of Profiles by Basin " + VAR, fontsize=16)
    plt.savefig('FIGURES/pie_basin_season_'+VAR+'.png', dpi=300)
    plt.close()

