from dotenv import load_dotenv
import openai
import os
import pandas as pd
import json
from tqdm import tqdm
import tiktoken

def load_env():
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("OPENAI API KEY NOT FOUND. CHECK YOUR .env FILE")
        return None
    
def load_data(file_path):
    return pd.read_csv(file_path)[["ID", "Body", "Link"]]

def round_embedding(embedding, decimal=6):
    if embedding is None:
        return None
    return [round(float(value), decimal) for value in embedding]

def make_batch(df, output_dir, batch_size, year):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    batch_dict = {"Invalid": []}
    
    for _, row in df.iterrows():
        if not (isinstance(row["Body"], str) and row["Body"].strip()):
            link = row["Link"] if "Link" in row and pd.notna(row["Link"]) else "No Link"
            print(f"Invalid text for {row['ID']}. Link: {link}")
            batch_dict["Invalid"].append(row["ID"])
    
    valid_ids = [row["ID"] for _, row in df.iterrows() if row["ID"] not in batch_dict["Invalid"]]
    
    for i in range(0, len(valid_ids), batch_size):
        batch_key = f"Batch_{str(i // batch_size).zfill(3)}"
        batch_dict[batch_key] = valid_ids[i:i+batch_size]
    
    output_file = os.path.join(output_dir, f"./Collection/Embeddings/Info/batches_info_{year}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(batch_dict, f, ensure_ascii=False, indent=4)
    
    print(f"Batches saved to {output_file}")

def estimate_token_count(text, model="text-embedding-3-small"):
    tokenizer = tiktoken.encoding_for_model(model)
    return len(tokenizer.encode(text))

def process_embeddings(df, model="text-embedding-3-small", max_tokens=7000):
    ID_list = df["ID"].tolist()
    link_list = df["Link"].tolist()
    text_list = df["Body"].tolist()

    if (len(ID_list) != len(link_list)) or (len(link_list) != len(text_list)):
        print("Something gone wrong...")
        return

    tokenizer = tiktoken.encoding_for_model(model)

    def truncate_text(text, max_tokens):
        tokens = tokenizer.encode(text)
        return tokenizer.decode(tokens[:max_tokens])
    
    token_counts = [estimate_token_count(text) for text in text_list]
    
    truncated_texts = [
        truncate_text(text, max_tokens) if token > max_tokens else text
        for text, token in zip(text_list, token_counts)
    ]
    
    batches = []
    tmp = []
    cumulative_token_count = 0

    embeddings = []
    for text, tokens in zip(truncated_texts, token_counts):
        if cumulative_token_count + tokens > max_tokens:
            batches.append(tmp)
            tmp = []
            cumulative_token_count = 0
        tmp.append(text)
        cumulative_token_count += tokens

    if tmp:
        batches.append(tmp)

    for batch in batches:
        try:
            response = openai.embeddings.create(
                model=model,
                input=batch
            )
            batch_embeddings = [round_embedding(item.embedding) for item in response.data]
            embeddings.extend(batch_embeddings)
        except Exception as e:
            embeddings.extend([None] * len(batch))

    result = [
        {"ID": ID_list[i],
         "Link": link_list[i],
         "Embedding": embeddings[i]}
         for i in range(len(ID_list))
    ]

    return result

def retry_failed_embeddings(file_path, df, model="text-embedding-3-small", max_tokens=7000):
    with open(file_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    id_to_text = {row["ID"]: row["Body"] for _, row in df.iterrows()}

    for item in results:
        if item["Embedding"] is None:
            id_val = item["ID"]
            text = id_to_text.get(id_val)
            if not text or not text.strip():
                print(f"No valid ID for {id_val}")
                continue

            token_count = estimate_token_count(text, model=model)
            if token_count > max_tokens:
                tokenizer = tiktoken.encoding_for_model(model)
                tokens = tokenizer.encode(text)
                text = tokenizer.decode(tokens[:max_tokens])

            try:
                response = openai.embeddings.create(
                    model=model,
                    input=[text]
                )
                new_embedding = round_embedding(response.data[0].embedding)
                item["Embedding"] = new_embedding
                print(f"ID {id_val} updating embedding succeed")
            except Exception as e:
                print(f"ID {id_val} updating embedding failed: {e}")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
