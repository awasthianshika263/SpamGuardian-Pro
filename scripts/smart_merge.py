import pandas as pd
import os
import glob
from hashlib import md5

DATASET_DIR = "dataset"
OUTPUT_FILE = os.path.join(DATASET_DIR, "master_dataset.csv")

print("Initializing dataset merge and deduplication...")

COLUMN_MAP = {
    "label": ["v1", "label", "spam", "category", "type", "phishing", "fraud", "class", "target"],
    "text": ["v2", "text", "message", "email", "body", "content", "email text", "subject", "mail"]
}

all_files = glob.glob(os.path.join(DATASET_DIR, "*.csv"))
dfs = []

for file in all_files:
    if "error" in file.lower():
        continue
    
    print(f"Processing: {os.path.basename(file)}")
    try:
        df = None
        for enc in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
            try:
                df = pd.read_csv(file, encoding=enc, on_bad_lines='skip')
                break
            except:
                continue
        
        if df is None:
            print("  [SKIP] Could not read file with any encoding")
            continue

        print(f"  Columns found: {df.columns.tolist()}")

        label_col = None
        text_col = None
        for std, candidates in COLUMN_MAP.items():
            for c in candidates:
                matches = [col for col in df.columns if c in col.lower()]
                if matches:
                    actual_col = matches[0]
                    if std == "label":
                        label_col = actual_col
                    else:
                        text_col = actual_col
                    break

        if (not label_col or not text_col) and len(df.columns) == 2:
            label_col = df.columns[0]
            text_col  = df.columns[1]
            print(f"  Auto-detected: label='{label_col}', text='{text_col}'")

        if not label_col or not text_col:
            print("  [SKIP] Label or text column not found")
            continue
        
        df = df[[label_col, text_col]].rename(columns={label_col: "label", text_col: "text"})
        df = df.dropna()
        df["text"] = df["text"].astype(str).str.strip()
        df = df[df["text"].str.len() > 10]
        
        df["label"] = df["label"].astype(str).str.lower()
        df["label"] = df["label"].apply(lambda x: "spam" if any(w in x for w in ["spam", "phishing", "fraud", "1"]) else "ham")

        if len(df) == 0:
            print("  [SKIP] 0 valid emails found")
            continue
        
        print(f"  [SUCCESS] Added {len(df):,} emails")
        dfs.append(df)
        
    except Exception as e:
        print(f"  [ERROR] Failed to process: {e}")

if dfs:
    print("\nMerging all datasets...")
    final_df = pd.concat(dfs, ignore_index=True)
    
    print("Removing duplicates using hash...")
    final_df["hash"] = final_df["text"].apply(lambda x: md5(x.encode()).hexdigest())
    before = len(final_df)
    final_df = final_df.drop_duplicates(subset=["hash"]).drop(columns=["hash"])
    after = len(final_df)

    # ← SIRF YAHAN CHANGE HUA HAI (1:1 balance)
    print("Balancing dataset (1 spam : 1 ham)...")
    spam = final_df[final_df["label"] == "spam"]
    ham  = final_df[final_df["label"] == "ham"]
    n    = min(len(spam), len(ham))
    spam = spam.sample(n=n, random_state=42)
    ham  = ham.sample(n=n, random_state=42)
    final_df = pd.concat([spam, ham]).sample(frac=1, random_state=42).reset_index(drop=True)
    
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nMASTER DATASET CREATED SUCCESSFULLY!")
    print(f"  • Before deduplication: {before:,}")
    print(f"  • After deduplication: {after:,}")
    print(f"  • Spam emails: {len(final_df[final_df['label']=='spam']):,}")
    print(f"  • Ham emails: {len(final_df[final_df['label']=='ham']):,}")
    print(f"  • File: {OUTPUT_FILE}")
else:
    print("No valid data found in dataset directory.")
