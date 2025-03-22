from Collection.Embeddings.utils import *
from Collection.Crawler.Stock.config import *
from argparse import ArgumentParser
import os
import json
from tqdm import tqdm

def create_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output_dir', type=str, required=False)
    parser.add_argument('-t', '--ticker_code', type=str, required=True, choices=TickerDict.keys())
    parser.add_argument('-y', '--year', type=str, required=True)
    return parser

def main():
    args = create_parser().parse_args()
    output_dir = args.output_dir if args.output_dir is not None else "./Data/News/Embeddings"
    ticker_code = args.ticker_code
    year = args.year

    # 1. Set data file path and load
    input_file = f"./Data/News/Processed/{ticker_code}_{year}.csv"
    load_env()
    df = load_data(input_file)
    
    # 2. Set batch JSON file path and create/load it
    batch_json_path = os.path.join(output_dir, f"./Collection/Embeddings/Info/batches_info_{year}.json")
    if not os.path.exists(batch_json_path):
        print("Batch JSON not found. Creating new batch JSON...")
        make_batch(df, output_dir, batch_size=20, year=year)
    else:
        print("Batch JSON file exists. Loading batch info...")
    with open(batch_json_path, "r", encoding="utf-8") as f:
        batch_info = json.load(f)

    # 3. Handle checkpoint file (for resuming after interruption)
    checkpoint_file = os.path.join(output_dir, f"checkpoint_{ticker_code}_{year}.json")
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            embeddings_result = json.load(f)
        print("Checkpoint file loaded. Resuming from checkpoint...")
    else:
        embeddings_result = []
        print("No checkpoint file found. Starting new embedding process...")

    # Construct list of already processed IDs
    processed_ids = set(item["ID"] for item in embeddings_result)
    # Sort only the "Batch_" keys for sequential processing (skip invalid keys)
    batch_keys = sorted([key for key in batch_info.keys() if key.startswith("Batch_")])

    # 4. Perform embedding for each batch
    for batch_key in tqdm(batch_keys, desc="Processing batches"):
        batch_ids = batch_info[batch_key]
        # Skip IDs already processed
        new_batch_ids = [bid for bid in batch_ids if bid not in processed_ids]
        if not new_batch_ids:
            continue

        # Extract subset of DataFrame corresponding to the batch
        batch_df = df[df["ID"].isin(new_batch_ids)]
        batch_result = process_embeddings(batch_df, model="text-embedding-3-small", max_tokens=7000)
        embeddings_result.extend(batch_result)
        processed_ids.update(new_batch_ids)
        
        # Save checkpoint after processing each batch
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(embeddings_result, f, ensure_ascii=False, indent=4)

    # 5. Retry failed embeddings
    print("Retrying failed embeddings...")
    retry_failed_embeddings(checkpoint_file, df, model="text-embedding-3-small", max_tokens=7000)
    print("Embedding processing complete.")

if __name__ == "__main__":
    main()
