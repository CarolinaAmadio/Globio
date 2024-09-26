#!/bin/bash

#SBATCH --job-name=checks
#SBATCH -N1
#SBATCH --ntasks-per-node=1
#SBATCH --time=02:30:00
#SBATCH --mem=300gb
#SBATCH --account=OGS_devC
#SBATCH --partition=g100_meteo_prod
#SBATCH --qos=qos_meteo


source /g100_work/OGS23_PRACE_IT/COPERNICUS/py_env_3.9.18/bin/activate
export PYTHONPATH=$PYTHONPATH:/g100_scratch/userexternal/camadio0/GLOBIO/bit.sea/src/
. ./opa_profile.inc


ONLINE_REPO=/g100_scratch/userexternal/camadio0/GLOBIO/
export ONLINE_REPO

DATASET=/g100_scratch/userexternal/camadio0/GLOBIO/SUPERFLOAT
UPDATE_FILE=Float_Index.txt
DIAG_DIR=$DATASET/oxy_diag


mkdir -p $DATASET $DIAG_DIR

#INPUTDIR='/g100_scratch/userexternal/camadio0/GLOBIO/CORIOLIS/'
#OUTDIR ='/g100_scratch/userexternal/camadio0/GLOBIO/'

opa_prex "python superfloat_discard.py -o $ONLINE_REPO/CORIOLIS/ -i  $ONLINE_REPO/CORIOLIS/"

opa_prex "python superfloat_chla_global.py     -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
opa_prex  "python superfloat_oxygen_global.py  -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE -O $DIAG_DIR"
rm -r $DIAG_DIR
opa_prex "python superfloat_nitrate_global.py  -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"


opa_prex "python superfloat_par_global.py      -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
opa_prex "python superfloat_bbp700_global.py   -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
opa_prex "python superfloat_ph_global.py       -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"

opa_prex "python dump_index.py -i $DATASET -o $DATASET/Float_Index.txt -t superfloat"

