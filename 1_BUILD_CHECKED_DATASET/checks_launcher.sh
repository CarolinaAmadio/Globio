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
export PYTHONPATH=$PYTHONPATH:/g100_work/OGS_devC/camadio/GLOBIO/Globio/1_BUILD_CHECKED_DATASET/bit.sea/src/
. ./opa_profile.inc


ONLINE_REPO=/g100_work/OGS_devC/camadio/GLOBIO/
export ONLINE_REPO

DATASET=/g100_work/OGS_devC/camadio/GLOBIO/SUPERFLOAT/
UPDATE_FILE=Float_Index.txt

mkdir -p $DATASET

opa_prex "python superfloat_chla_global.py     -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
#opa_prex  "python superfloat_oxygen_global.py  -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
#opa_prex "python superfloat_nitrate_global.py  -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"


#opa_prex "python superfloat_par_global.py      -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
#opa_prex "python superfloat_bbp700_global.py   -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"
#opa_prex "python superfloat_ph_global.py       -o $DATASET -u $ONLINE_REPO/CORIOLIS/$UPDATE_FILE"

#opa_prex "python dump_index.py -i $DATASET -o $DATASET/Float_Index.txt -t superfloat"

