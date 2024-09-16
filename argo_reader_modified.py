import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Read file argo, gives back same file without the header and index_col
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--inputfile',"-i",
                                type = str,
                                required = True,
                                help = 'input file argo txt, eg=')
    parser.add_argument(   '--outfile',"-o",
                                type = str,
                                required = True,
                                help = 'output file argo')
    return parser.parse_args()

args = argument()



import numpy as np
import pandas as pd

input_file = args.inputfile
output_file  = args.outfile

df = pd.read_csv(input_file, header=8)
df=df.iloc[:,:]
df.to_csv(output_file, header=False, index=False, sep=',')

