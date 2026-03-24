import sys

from src.download import download_dataset
from src.reports import generate_silver_report
from src.transform import transform
from src.config import RAW_DIR, SILVER_DIR, DATASET_NAME

def run_pipeline():
    try:
        print("\n[Step 1] Downloading raw data...")
        download_dataset(DATASET_NAME, RAW_DIR)

        print("\n[Step 2] Transforming data...")
        transform(RAW_DIR, SILVER_DIR)

        print("\n[Step 3] Generating report over transformed data...")
        generate_silver_report()

    except Exception as e:
        print(f"\n Pipeline error: {e}")
        sys.exit(1)

run_pipeline()