import pandas as pd
import io
from sqlalchemy import create_engine

from src.config import SILVER_DIR, logger, DB_URL

PATH_SILVER = SILVER_DIR
DB_URL = DB_URL

def clean_timestamp_col(df, column_name):
    df[column_name] = pd.to_datetime(df[column_name], errors='coerce', utc=True)
    null_count = df[column_name].isna().sum()

    if null_count > 0:
        logger.warning(f"{null_count} null records in {column_name} column.")

    return df

def run_etl_gold():
    try:
        engine = create_engine(DB_URL)

        logger.info("Processing data from silver->gold")
        df = load_customers()
        load_to_postgres(df, "customers", engine)

        df = load_sellers()
        load_to_postgres(df, "sellers", engine)

        df = load_orders()
        load_to_postgres(df, "orders", engine)

        df = load_order_items()
        load_to_postgres(df, "order_items", engine)

        logger.info("Success processing files.")
    except Exception as e:
        logger.error(f"Pipeline critical error: {e}")
        raise

def load_customers():
    df_customers = pd.read_parquet(f"{PATH_SILVER}/customers.parquet")

    mapping = {
        'customer_id': 'customer_unique_id',
    }

    df_gold = df_customers[list(mapping.keys())].rename(columns=mapping)
    initial_count = len(df_gold)
    df_new = df_gold.drop_duplicates(subset=['customer_unique_id'])
    end_count = len(df_new)

    if initial_count > end_count:
        logger.warning(f"Discarded {initial_count - end_count} duplicates")

    return df_new


def load_sellers():
    df_sellers = pd.read_parquet(f"{PATH_SILVER}/sellers.parquet")

    mapping = {
        'seller_id': 'seller_id',
        'seller_city': 'city',
        'seller_state': 'state',
        'seller_zip_code_prefix': 'zip_code_prefix',
    }

    df_gold = df_sellers[list(mapping.keys())].rename(columns=mapping)
    initial_count = len(df_gold)
    df_gold.drop_duplicates(subset=['seller_id'])
    end_count = len(df_gold)

    if end_count < initial_count:
        logger.warning(f"Discarded {initial_count - end_count} duplicates")

    return df_gold


def load_orders():
    df_orders = pd.read_parquet(f"{PATH_SILVER}/orders.parquet")
    df_customers = pd.read_parquet(f"{PATH_SILVER}/customers.parquet")
    df_items = pd.read_parquet(f"{PATH_SILVER}/order_items.parquet")

    # df_address_lookup = df_customers[[
    #     'customer_id',
    #     'customer_zip_code_prefix',
    #     'customer_city',
    #     'customer_state',
    # ]]

    df_enriched = pd.merge(
        df_orders,
        df_customers,
        on='customer_id',
        how='left'
    )

    # sum total price and total freight
    df_items_sum = df_items.groupby('order_id')['price'].sum().reset_index()
    df_items_sum = df_items_sum.rename(columns={'price': 'total_price'})
    df_freight_sum = df_items.groupby('order_id')['freight_value'].sum().reset_index()
    df_freight_sum = df_freight_sum.rename(columns={'freight_value': 'total_freight'})

    df_enriched = pd.merge(df_enriched, df_items_sum, on='order_id', how='left')
    df_enriched = pd.merge(df_enriched,df_freight_sum,on='order_id',how='left')


    mapping = {
        'order_id': 'order_id',
        'customer_id': 'customer_unique_id',
        'order_status': 'status',
        'order_approved_at': 'approved_at',
        'order_purchase_timestamp': 'purchased_at',
        'customer_zip_code_prefix': 'delivery_prefix_zip_code',
        'customer_city': 'delivery_city',
        'customer_state': 'delivery_state',
        'order_delivered_carrier_date': 'delivered_carrier_date',
        'order_delivered_customer_date': 'delivered_customer_date',
        'order_estimated_delivery_date': 'estimated_delivery_date',
        'total_price': 'total_price',
        'total_freight': 'total_freight',
    }

    df_enriched = clean_timestamp_col(df_enriched, "order_approved_at")

    df_gold = df_enriched[list(mapping.keys())].rename(columns=mapping)
    initial_count = len(df_gold)
    df_gold.drop_duplicates(subset=['order_id'])
    end_count = len(df_gold)

    if end_count < initial_count:
        logger.warning(f"Discarded {initial_count - end_count} duplicates")

    return df_gold

def load_order_items():
    df_items = pd.read_parquet(f"{PATH_SILVER}/order_items.parquet")
    df_products = pd.read_parquet(f"{PATH_SILVER}/products.parquet")

    mapping = {
        'order_id': 'order_id',
        'order_item_id': 'order_item_id',
        'product_category_name': 'product_category',
        'seller_id': 'seller_id',
        'shipping_limit_date': 'shipping_limit_date',
        'price': 'price',
        'freight_value': 'freight_value'
    }

    df_enriched = pd.merge(
        df_items,
        df_products[['product_id', 'product_category_name', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']],
        on='product_id',
        how='left'
    )

    df_gold = df_enriched[list(mapping.keys())].rename(columns=mapping)
    initial_count = len(df_gold)
    df_gold.drop_duplicates(subset=['order_id'])
    end_count = len(df_gold)

    if end_count < initial_count:
        logger.warning(f"Discarded {initial_count - end_count} duplicates")

    return df_gold

def load_to_postgres(df, table_name, engine):
    logger.info(f"Loading data into table '{table_name}'")
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)

    conn = engine.raw_connection()
    try:
        with conn.cursor() as cursor:
            sql = f"COPY gold.{table_name} FROM STDIN WITH (FORMAT CSV, DELIMITER '\t')"
            cursor.copy_expert(sql, output)
            conn.commit()
            logger.info(f"Load finished. {len(df)} rows inserted.")
    finally:
        conn.close()

if __name__ == '__main__':
    run_etl_gold()