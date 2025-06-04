import pandas as pd
import glob
from argparse import ArgumentParser
import sys
import os

def main(path, source, output_path): 

    all_files = glob.glob(f'{path}/{source}_batches/*.csv')
    df_list = []

    for file in all_files:
        try:
            temp_df = pd.read_csv(file)
            df_list.append(temp_df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    merged_df = pd.concat(df_list, ignore_index= True)
    
    sub_folder = "company_info" if source == "sam" or "company_info" in source else "funding"
    

    filepath = f'{output_path}/uncleaned_outputs/{sub_folder}'

    if not os.path.exists(filepath): 
        os.makedirs(filepath)

    substring = "_".join(source.split("_")[:2]) if source.startswith("usas") and source != "usas_company_info" else source.split("_")[0]

    merged_df.to_csv(f'{filepath}/{substring}_uncleaned.csv', index=False)
    
    #os.system(f"rm -R {path}/{source}_batches/")


def parse_args(arglist):
    parser = ArgumentParser()
    parser.add_argument("--root_path", "-r", required=True, help="Root Path")
    parser.add_argument("--source" ,"-s" , required=True, help="Source File Name" )
    parser.add_argument("--output_path" ,"-o" , required=True, help="output_path" )
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.root_path, args.source, args.output_path)
