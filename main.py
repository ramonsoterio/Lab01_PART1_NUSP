import sys

from src.download import download_dataset
from src.etl_gold import run_etl_gold
from src.reports import generate_silver_report
from src.transform import transform

from src.config import RAW_DIR, SILVER_DIR, DATASET_NAME, logger

def run_pipeline():
    try:
        logger.info("\n[Step 1] Downloading raw data...")
        download_dataset(DATASET_NAME, RAW_DIR)

        logger.info("\n[Step 2] Transforming data...")
        transform(RAW_DIR, SILVER_DIR)

        logger.info("\n[Step 3] Generating report over transformed data...")
        generate_silver_report()

        logger.info("\n[Step 4] Generate golden data...")
        run_etl_gold()

        logger.info("\nETL pipeline successfully completed.")
    except Exception as e:
        logger.info(f"\n Pipeline error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_pipeline()