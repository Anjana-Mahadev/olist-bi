# src/agents/sql_worker.py
from src.database import execute_query
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.config import get_settings

settings = get_settings()

class SQLWorker:
    def __init__(self):
        # LLM to convert natural questions into SQL
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0
        )

    def run(self, state: dict):
        question = state.get("question", "")

        # Generate SQL using LLM
        prompt = f"""
        You are an expert SQL generator for an SQLite database.

        Database tables:
        - sellers(seller_id, seller_zip_code_prefix, seller_city, seller_state)
        - product_category_name_translation(product_category_name, product_category_name_english)
        - orders(order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
        - products(product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm)
        - order_reviews(review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp)
        - geolocation(geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)
        - order_items(order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
        - customers(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
        - order_payments(order_id, payment_sequential, payment_type, payment_installments, payment_value)

        Generate a valid SQLite query for the following user question:
        {question}

        Only provide the SQL query as the output.
        """

        response = self.llm.invoke([HumanMessage(content=prompt)])
        sql_query = response.content.strip()

        # Remove code block markers if present
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        # Execute SQL
        db_result = execute_query(sql_query)

        return {
            **state,
            "sql_query": sql_query,
            "db_result": db_result
        }