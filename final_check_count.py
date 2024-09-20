# total profiles in: 


#1. argo_synthetic-profile_index.txt:                    322569 
#2. argo_synthetic-profile_index_CORR.txt                306633 (no descend e no with blanks coord latlon in 1.)


#3. in CORIOLIS/download/Global_floats.txt               306624 (no header rispetto a 2.)
#4. in CORIOLIS/Float_Index_0.txt                        306624 
#5. CORIOLIS/Float_Index.txt                             306624

#6. CORIOLIS/download/tmp                                306731
#7. files_downloaded_but_not_in_float_index.csv             108 
#8. files_in_float_index_BUT_not_downloaded.csv               0

# devo capire il perche di 107 in piu scaricati e non in float index
# in teoria aoml ha sia file sr che sd scaricabili 

# The goal of the script is to check the hypothesis


import pandas as pd
import os
import shutil

df=pd.read_csv('files_downloaded_but_not_in_float_index.csv')

directory = 'CORIOLIS/download/duplicates'
if not os.path.exists(directory):
    os.makedirs(directory)
    print(f"Directory '{directory}' created.")
else:
    print(f"Directory '{directory}' already exists.")

III=0
for FILE in df.Filename:
    tmp = 'SD' + FILE[2:]
    tmp = 'CORIOLIS/download/tmp/'+tmp
    if os.path.exists(tmp):
       print(f"{tmp} exists.")
       shutil.move('CORIOLIS/download/tmp/'+ FILE, directory)
       III+=1
    else:
       import sys
       sys.exit(f"{tmp} does not exist.")

file_count = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
print(file_count)
print(len(df ))

