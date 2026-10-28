# Activate the Python virtual environment
source /g100/home/userexternal/camadio0/envs/py38_seaborn/bin/activate

# add bitsea to the PYTHONPAH
export PYTHONPATH=/g100_scratch/userexternal/camadio0/GLOBIO_AG/bit.sea/src:$PYTHONPATH

OUTDIR=SUPERFLOAT


mkdir -p $OUTDIR

python 00_download_data_save_netcdf.py -o $OUTDIR
python dump_index.py -i $OUTDIR -o $OUTDIR/Float_Index.txt -t superfloat


