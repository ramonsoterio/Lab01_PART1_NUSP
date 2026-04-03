CREATE SCHEMA IF NOT EXISTS gold;

CREATE TYPE gold.order_status AS ENUM (
    'delivered',
    'invoiced',
    'shipped',
    'processing',
    'unavailable',
    'canceled',
    'created',
    'approved'
);


DROP TABLE IF EXISTS gold.order_items;
DROP TABLE IF EXISTS gold.orders;
DROP TABLE IF EXISTS gold.customers;
DROP TABLE IF EXISTS gold.sellers;

CREATE TABLE IF NOT EXISTS gold.sellers (
    seller_id UUID PRIMARY KEY NOT NULL,
    city VARCHAR(255) NOT NULL,
    state CHAR(2) NOT NULL,
    zip_code_prefix VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS gold.customers (
    customer_id UUID PRIMARY KEY NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.orders (
    order_id UUID PRIMARY KEY NOT NULL,
    customer_id UUID NOT NULl,
    status gold.order_status NOT NULL,
    approved_at DATE,
    purchased_at TIMESTAMPTZ NOT NULL,
    delivery_prefix_zip_code VARCHAR(25),
    delivery_city VARCHAR(255),
    delivery_state VARCHAR(255),
    delivered_carrier_date TIMESTAMPTZ,
    delivered_customer_date TIMESTAMPTZ,
    estimated_delivery_date TIMESTAMPTZ,
    total_price NUMERIC(15,2),
    total_freight NUMERIC(15,2),

    CONSTRAINT fk_customer
        FOREIGN KEY(customer_id)
        REFERENCES gold.customers(customer_id)
);

CREATE TABLE IF NOT EXISTS gold.order_items (
    order_id UUID NOT NULL,
    order_item_id INT NOT NULL,
    product_category VARCHAR(255) NOT NULL,
    seller_id UUID NOT NULL,
    shipping_limit_date TIMESTAMPTZ,
    price NUMERIC(15,2),
    freight_value NUMERIC(15,2),

    PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT fk_order
        FOREIGN KEY (order_id)
        REFERENCES gold.orders(order_id),

    CONSTRAINT fk_seller
        FOREIGN KEY (seller_id)
        REFERENCES gold.sellers(seller_id)
);