import sys
import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    add to the float ondex the column of datamode
    default= all vars in Delayed mode
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--ofile','-o',
                                type = str,
                                required = True,
                                help = 'Float_index.txt if overwrite')
    parser.add_argument(   '--ifile','-i',
                                type = str,
                                required = True,
                                help = ''' Float_index.txt''')
    parser.add_argument(   '--data_type', '-type',
                                type=str,
                                required=False,
                                default='D',  
                                help='String to repeat for each variable (default: D)'
                       )

    return parser.parse_args()


args = argument()
import pandas as pd

file_path   = args.ifile
output_path = args.ofile
data_type   = args.data_type

# Leggi ogni riga del float index
with open(file_path, "r") as f:
    lines = f.readlines()

output_lines = []
for line in lines:
    parts = line.strip().split(",")
    base_info = parts[:4]  # Prendi i primi quattro campi
    variables = parts[4]  # La colonna con le variabili
    num_variables = len(variables.split())  # Conta quante sono
    sigla_D = data_type * num_variables  # Ripeti  data_type tante volte quante sono le variabili
    output_line = ",".join(parts) + f", {sigla_D}"  # Aggiungi la nuova colonna
    output_lines.append(output_line)

with open(output_path, "w") as f:
    f.write("\n".join(output_lines))


