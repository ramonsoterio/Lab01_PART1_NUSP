import pandas as pd
import json
from src.config import TABLE_MAP, STATS_DIR

def transform(source_dir, destination_dir):
    meta_dir = STATS_DIR
    meta_dir.mkdir(parents=True, exist_ok=True)

    for raw_name, silver_name in TABLE_MAP.items():
        raw_file = source_dir / f"{raw_name}.csv"
        if raw_file.exists():
            df_raw = pd.read_csv(raw_file)
            df_result = clean_df(df_raw)

            metadata = {
                "columns": df_result.columns.tolist(),
                "types": df_result.dtypes.astype(str).to_dict(),
                "nulls": df_result.isnull().sum().to_dict(),
                "rows": len(df_result),
            }
            with open(meta_dir / f"{silver_name}_meta.json", "w") as f:
                json.dump(metadata, f)

            df_result.to_parquet(destination_dir / f"{silver_name}.parquet", index=False)


def clean_df(df):
    df = to_snake_case(df)
    df = df.drop_duplicates()

    date_cols = [col for col in df.columns if 'timestamp' in col or 'date' in col]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    cat_cols = df.select_dtypes(include=['object']).columns
    df[cat_cols] = df[cat_cols].fillna("N/A")

    return df

def to_snake_case(df):
    df.columns = (df.columns
                  .str.replace('(?<=[a-z])(?=[A-Z])', '_', regex=True)
                  .str.replace(' ', '_')
                  .str.lower())
    return df