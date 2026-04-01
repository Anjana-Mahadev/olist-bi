import re
from typing import Dict, List, Set


SCHEMA_CATALOG: Dict[str, List[str]] = {
	"sellers": ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
	"product_category_name_translation": ["product_category_name", "product_category_name_english"],
	"orders": [
		"order_id",
		"customer_id",
		"order_status",
		"order_purchase_timestamp",
		"order_approved_at",
		"order_delivered_carrier_date",
		"order_delivered_customer_date",
		"order_estimated_delivery_date",
	],
	"products": [
		"product_id",
		"product_category_name",
		"product_name_lenght",
		"product_description_lenght",
		"product_photos_qty",
		"product_weight_g",
		"product_length_cm",
		"product_height_cm",
		"product_width_cm",
	],
	"order_reviews": [
		"review_id",
		"order_id",
		"review_score",
		"review_comment_title",
		"review_comment_message",
		"review_creation_date",
		"review_answer_timestamp",
	],
	"geolocation": [
		"geolocation_zip_code_prefix",
		"geolocation_lat",
		"geolocation_lng",
		"geolocation_city",
		"geolocation_state",
	],
	"order_items": [
		"order_id",
		"order_item_id",
		"product_id",
		"seller_id",
		"shipping_limit_date",
		"price",
		"freight_value",
	],
	"customers": ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"],
	"order_payments": ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"],
}

TABLE_KEYWORDS = {
	"orders": ["order", "orders", "delivery", "delivered", "purchase", "status", "shipping"],
	"order_items": ["item", "items", "price", "freight", "shipping", "revenue", "sales"],
	"products": ["product", "products", "category", "categories"],
	"product_category_name_translation": ["category", "categories", "translation"],
	"customers": ["customer", "customers", "buyer", "buyers", "city", "state", "region"],
	"sellers": ["seller", "sellers", "merchant", "merchants"],
	"order_payments": ["payment", "payments", "installment", "revenue", "paid"],
	"order_reviews": ["review", "reviews", "rating", "score", "satisfaction"],
	"geolocation": ["geolocation", "latitude", "longitude", "zip", "state", "city", "location"],
}

DEFAULT_TABLES = ["orders", "order_items", "products", "customers", "order_payments", "order_reviews"]
FORBIDDEN_SQL_PATTERNS = [
	r"\binsert\b",
	r"\bupdate\b",
	r"\bdelete\b",
	r"\bdrop\b",
	r"\balter\b",
	r"\bcreate\b",
	r"\battach\b",
	r"\bpragma\b",
	r"\breindex\b",
	r"\bvacuum\b",
]


def select_tables_for_question(question: str) -> List[str]:
	text = question.lower()
	selected: Set[str] = set()

	for table_name, keywords in TABLE_KEYWORDS.items():
		if any(keyword in text for keyword in keywords):
			selected.add(table_name)

	if not selected:
		selected.update(DEFAULT_TABLES)

	if {"products", "sellers", "order_payments", "order_reviews"} & selected:
		selected.add("order_items")
		selected.add("orders")

	if "products" in selected and "product_category_name_translation" not in selected and "category" in text:
		selected.add("product_category_name_translation")

	if "customers" in selected and any(token in text for token in ["city", "state", "zip", "location"]):
		selected.add("geolocation")

	return [table_name for table_name in SCHEMA_CATALOG if table_name in selected]


def format_schema_context(selected_tables: List[str]) -> str:
	lines = []
	for table_name in selected_tables:
		columns = SCHEMA_CATALOG.get(table_name, [])
		if columns:
			lines.append(f"- {table_name}({', '.join(columns)})")
	return "\n".join(lines)


def sanitize_sql(sql_query: str) -> str:
	cleaned = sql_query.replace("```sql", "").replace("```", "").strip()
	return cleaned.rstrip(";").strip()


def extract_referenced_tables(sql_query: str) -> Set[str]:
	cleaned = sanitize_sql(sql_query)
	cte_names = set(re.findall(r"(?:with|,)\s*([a-zA-Z_][\w]*)\s+as\s*\(", cleaned, flags=re.IGNORECASE))
	referenced = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", cleaned, flags=re.IGNORECASE))
	return {table_name for table_name in referenced if table_name not in cte_names}


def should_limit_results(sql_query: str) -> bool:
	lowered = sql_query.lower()
	aggregate_tokens = [" count(", " sum(", " avg(", " min(", " max(", " group by ", " distinct "]
	return " limit " not in lowered and not any(token in lowered for token in aggregate_tokens)


def validate_sql_query(sql_query: str, allowed_tables: List[str]) -> Dict[str, object]:
	errors: List[str] = []
	cleaned = sanitize_sql(sql_query)

	if not cleaned:
		errors.append("The SQL generator returned an empty query.")
		return {"valid": False, "sanitized_query": cleaned, "errors": errors, "referenced_tables": []}

	lowered = f" {cleaned.lower()} "

	if any(re.search(pattern, lowered) for pattern in FORBIDDEN_SQL_PATTERNS):
		errors.append("Only read-only SELECT queries are allowed.")

	if not (cleaned.lower().startswith("select") or cleaned.lower().startswith("with")):
		errors.append("The query must start with SELECT or WITH.")

	if ";" in cleaned:
		errors.append("Multiple SQL statements are not allowed.")

	referenced_tables = sorted(extract_referenced_tables(cleaned))
	disallowed_tables = [table_name for table_name in referenced_tables if table_name not in set(allowed_tables)]
	if disallowed_tables:
		errors.append(f"The query referenced tables outside the selected schema: {', '.join(disallowed_tables)}.")

	if not errors and should_limit_results(cleaned):
		cleaned = f"{cleaned} LIMIT 200"

	return {
		"valid": not errors,
		"sanitized_query": cleaned,
		"errors": errors,
		"referenced_tables": referenced_tables,
	}
