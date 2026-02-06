SCHEMA = """
Database: Brazilian E-Commerce (SQLite)

Tables and Columns:

customers
- customer_id (PRIMARY KEY)
- customer_unique_id
- customer_zip_code_prefix
- customer_city
- customer_state

orders
- order_id (PRIMARY KEY)
- customer_id (FOREIGN KEY → customers.customer_id)
- order_status
- order_purchase_timestamp
- order_approved_at
- order_delivered_carrier_date
- order_delivered_customer_date
- order_estimated_delivery_date

order_items
- order_item_id
- order_id (FOREIGN KEY → orders.order_id)
- product_id (FOREIGN KEY → products.product_id)
- seller_id (FOREIGN KEY → sellers.seller_id)
- shipping_limit_date
- price
- freight_value

payments
- order_id (FOREIGN KEY → orders.order_id)
- payment_sequential
- payment_type
- payment_installments
- payment_value

products
- product_id (PRIMARY KEY)
- product_category_name
- product_weight_g
- product_length_cm
- product_height_cm
- product_width_cm

sellers
- seller_id (PRIMARY KEY)
- seller_zip_code_prefix
- seller_city
- seller_state

geolocation
- geolocation_zip_code_prefix
- geolocation_lat
- geolocation_lng
- geolocation_city
- geolocation_state

order_reviews
- review_id (PRIMARY KEY)
- order_id (FOREIGN KEY → orders.order_id)
- review_score
- review_comment_title
- review_comment_message
- review_creation_date
- review_answer_timestamp

"""
