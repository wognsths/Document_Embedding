from Collection.Preprocess.News.utils import *
import pandas as pd
import os
from tqdm import tqdm

        
def main():
    raw_dir = os.path.join(os.curdir, "Data", "News", "Raw")
    processed_dir = os.path.join(os.curdir, "Data", "News", "Processed")
    
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
    file_list = [os.path.join(raw_dir, file) for file in os.listdir(raw_dir) if file.endswith('.csv')]
    
    for file in tqdm(file_list, desc="Processing files"):
        print(f"Processing file: {file}")
        df = pd.read_csv(file, encoding="utf-8")
        df.drop_duplicates(subset=["Link"], inplace=True)
        df["Ignore"] = 0
        
        df["Title"] = df["Title"].apply(convert_hanja)
        df["Body"] = df["Body"].apply(convert_hanja)
        
        df["Category"] = (df["Title"] + df["Body"]).apply(categorize_document)
        
        df["Body"] = df["Body"].apply(process_body)
        df["Body"] = df["Body"].apply(remove_special_characters)
        
        df["ID"] = df["Date"].astype(str) + "_" + (df.groupby("Date").cumcount() + 1).astype(str).str.zfill(3)

        df.loc[df["Body"].isna(), "Ignore"] = 1
        
        output_file = os.path.join(processed_dir, os.path.basename(file))
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Saved processed file: {output_file}")

if __name__ == "__main__":
    main()