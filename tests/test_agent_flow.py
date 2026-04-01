from app import flask_app
from src.agents.router_worker import router_node
from src.agents.schema_selector import schema_selector_node
from src.graph import app as graph_app
from src.tools.sql_tools import validate_sql_query


def test_router_detects_greeting():
    state = router_node({"question": "hello there"})
    assert state["intent"] == "greeting"


def test_schema_selector_chooses_review_tables():
    state = schema_selector_node({"question": "Which product categories have the worst review scores?"})
    assert "products" in state["selected_tables"]
    assert "order_reviews" in state["selected_tables"]
    assert "order_items" in state["selected_tables"]


def test_validate_sql_query_rejects_disallowed_table():
    result = validate_sql_query("SELECT * FROM secret_table", ["orders"])
    assert result["valid"] is False
    assert result["errors"]


def test_validate_sql_query_adds_limit_for_row_queries():
    result = validate_sql_query("SELECT order_id FROM orders", ["orders"])
    assert result["valid"] is True
    assert result["sanitized_query"].endswith("LIMIT 200")


def test_graph_handles_greeting_without_data_agents():
    result = graph_app.invoke({"question": "hi"})
    assert result["response_type"] == "greeting"
    assert result["final_answer"]


def test_flask_query_endpoint_handles_greeting():
    client = flask_app.test_client()
    response = client.post("/query", json={"question": "hi"})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "success"
    assert payload["type"] == "greeting"