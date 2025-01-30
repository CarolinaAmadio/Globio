import argparse
import pandas as pd

def compare_first_column_to_dataframe(file1_path, file2_path, output_path):
    # Leggi il contenuto dei file
    with open(file1_path, 'r') as f1:
        file1_lines = [line.split(",")[0].strip() for line in f1.readlines()]
    
    with open(file2_path, 'r') as f2:
        file2_lines = [line.split(",")[0].strip() for line in f2.readlines()]
    
    # Dataframe per salvare le differenze
    diff_df = pd.DataFrame(columns=["Namefile", "Motiv", "FirstVar"])

    # Confronta e aggiungi al dataframe se non è presente in file2
    for line in file1_lines:
        if line not in file2_lines:
            diff_df = diff_df.append({"Namefile": line, "Motiv": "latlon_ir_Descend", "FirstVar": ""}, ignore_index=True)
    
    print('nr of profiles in the downloaded dataset: \n')
    print(len(file1_lines))
    print('Float index new len: \n')
    print(len(file2_lines))
    print('difference: \n')
    print(len(diff_df))
    
    diff_df.to_csv(output_path, index=False, header=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Confronta la prima colonna di due file Float Index e genera un file di differenze.")
    parser.add_argument("-i1", "--input1", required=True, help="Percorso al primo file di input (Float_Index_0.txt).")
    parser.add_argument("-i2", "--input2", required=True, help="Percorso al secondo file di input (Float_Index.txt).")
    parser.add_argument("-o", "--output", required=True, help="Percorso al file di output (diff.txt).")
    args = parser.parse_args()

    compare_first_column_to_dataframe(args.input1, args.input2, args.output)

