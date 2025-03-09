import pandas as pd
import glob
from argparse import ArgumentParser
import sys

def main(path, source): 

    all_files = glob.glob(f'{path}/{source}_batches/*batch*.csv')
    df_list = []

    for file in all_files:
        try:
            temp_df = pd.read_csv(file)
            df_list.append(temp_df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    merged_df = pd.concat(df_list, ignore_index= True)
    merged_df.to_csv(f'{path}/merged_files/{source}_uncleaned.csv', index=False)


def parse_args(arglist):
    parser = ArgumentParser()
    parser.add_argument("--root_path", "-r", required=True, help="Root Path")
    parser.add_argument("--source" ,"-s" , required=True, help="Source File Name" )
    return parser.parse_args(arglist)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args.root_path, args.source)
