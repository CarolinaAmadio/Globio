import sys
sys.path.append("/g100/home/userexternal/camadio0/CA_functions/")
import pandas as pd
import numpy as np
from funzioni_CA import globe_Map
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from bitsea.instruments.var_conversions import FLOATVARS

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


III = 0
for VAR in varlist:
    vv = FLOATVARS[VAR]
    #vv = VARLIST[III]
    df = pd.read_csv(INPUTDIR + INDEXTXT + VAR + '__' + vv + '.csv', index_col=0)
    III+=1
    df["basin"] = df["basin"].replace("Mare Continentale o Indefinito", "Marginal Seas")
    ADD_season(df)

    LEN= len(df)
    df1 = df.groupby(by='basin').count()
    df1.reset_index(inplace=True)
    df2 = df1[['basin','n_profiles_per_day']]

    fig= plt.subplots(figsize=(15, 8))
    plt.grid(color='grey', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.bar(df2["basin"], df2.n_profiles_per_day, color='cyan', alpha=0.8, edgecolor='black')
    plt.xlabel("Basin", fontsize=14)
    plt.ylabel("Number of Profiles", fontsize=14)
    plt.title("Number of Profiles per Basin", fontsize=16)
    plt.xticks(rotation=90, ha="right", fontsize=12)
    plt.tight_layout()
    plt.savefig('FIGURES/'+'basin_distribution_'+VAR+'.png', dpi=300)
    plt.close()

    fig= plt.subplots(figsize=(15, 8))
    plt.grid(color='grey', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.bar(df2["basin"], (df2.n_profiles_per_day/len(df))*100, color='cyan', alpha=0.8, edgecolor='black')
    plt.xlabel("Basin", fontsize=14)
    plt.ylabel("% Profiles", fontsize=14)
    plt.title("Percentage of Profiles per Basin", fontsize=16)
    plt.xticks(rotation=90, ha="right", fontsize=12)
    plt.tight_layout()
    plt.savefig('FIGURES/'+'basin_distribution_percent_'+VAR+'.png', dpi=300)
    plt.close()


    plt.figure(figsize=(10, 10))
    plt.pie(
    df2["n_profiles_per_day"],
    labels=df2["basin"],
    autopct='%1.1f%%',  # Mostra percentuali con una cifra decimale
    startangle=90,      # Inizio a 90 gradi
    #colors=plt.cm.tab20.colors
    colors=plt.cm.Pastel1.colors # Usa una mappa di colori
    )
    plt.title("Distribution of Profiles by Basin", fontsize=16)
