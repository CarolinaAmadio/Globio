import pandas as pd
import glob
import os
import multiprocessing

DIR_INDEX_FILE = "/g100_work/OGS_devC/camadio/GLOBIO/CORIOLIS/"

# Funzione globale per controllare se un file esiste nella directory
def check_file_exists(args):
    filename, dir_path = args
    outfile = os.path.join(dir_path, filename)
    if not os.path.exists(outfile):
        return filename
    return None

# Funzione globale per controllare se un file è nella lista dei file
def check_file_in_list(args):
    filename, file_list = args
    if filename not in file_list:
        return filename
    return None

def main():
    df = pd.read_csv('/g100_work/OGS_devC/camadio/GLOBIO/CORIOLIS/download/Global_floats.txt', header=None, sep=',')
    columns = ['file', 'date', 'latitude', 'longitude', 'ocean', 'profiler_type', 'institution', 'parameters', 'parameter_data_mode', 'date_update']
    df.columns = columns

    df['WMO'] = df['file'].str.split('/').str[1]
    df['profiles'] = df['file'].str.split('/').str[-1]

    dir_path = '/g100_work/OGS_devC/camadio/GLOBIO/CORIOLIS/download/tmp'
    file_list = df['profiles'].tolist()

    # Prepara gli argomenti per il pool
    file_exists_args = [(f, dir_path) for f in file_list]

    # Verifica dei file nella directory
    with multiprocessing.Pool() as pool:
        in_float_index_not_downloaded = pool.map(check_file_exists, file_exists_args)

    in_float_index_not_downloaded = [f for f in in_float_index_not_downloaded if f]

    # Lista dei file nella directory
    LISTFILE = glob.glob(os.path.join(dir_path, '*nc'))
    LISTFILE = [os.path.basename(f) for f in LISTFILE]

    # Prepara gli argomenti per il pool
    file_in_list_args = [(f, file_list) for f in LISTFILE]

    # Verifica dei file nel dataframe
    with multiprocessing.Pool() as pool:
        downloaded_not_in_float_index = pool.map(check_file_in_list, file_in_list_args)

    downloaded_not_in_float_index = [f for f in downloaded_not_in_float_index if f]

    # Salvare i risultati
    df_downloaded_not_in_float_index = pd.DataFrame(downloaded_not_in_float_index, columns=['Filename'])
    df_downloaded_not_in_float_index.to_csv('/g100_work/OGS_devC/camadio/GLOBIO/files_downloaded_but_not_in_float_index.csv', index=False)

    df_in_float_index_not_downloaded = pd.DataFrame(in_float_index_not_downloaded, columns=['Filename'])
    df_in_float_index_not_downloaded.to_csv('/g100_work/OGS_devC/camadio/GLOBIO/files_in_float_index_BUT_not_downloaded.csv', index=False)

if __name__ == '__main__':
    main()

