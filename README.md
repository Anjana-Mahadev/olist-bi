
# 🚀 Olist Multi-Agent BI System

A Python-based multi-agent Business Intelligence (BI) system for the **Olist e-commerce dataset**. This project allows users to ask natural language questions about Olist data, automatically generates SQL queries, executes them on the database, and provides insightful business analysis.

---

## Multi-Agent Flow Diagram

```text
        ┌───────────────────┐
        │   User Question   │
        └────────┬──────────┘
                 │
                 ▼
        ┌───────────────────┐
        │   Orchestrator    │
        │ (Coordinates Agents)│
        └────────┬──────────┘
                 │
      ┌──────────┴───────────┐
      │                      │
      ▼                      ▼
┌─────────────────┐     ┌──────────────────┐
│   SQL Worker    │     │  Analyst Worker  │
│ (Generates SQL, │     │ (Analyzes SQL    │
│ Executes Query) │     │ Results & LLM)   │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └──────────┬────────────┘
                    ▼
        ┌───────────────────┐
        │   Final Answer    │
        │ (SQL + Insights)  │
        └───────────────────┘

```

## 📂 Repository Structure

```text
.
├── data/
│   ├── olist_customers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   └── product_category_name_translation.csv
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── analyst_worker.py
│   │   ├── orchestrator.py
│   │   └── sql_worker.py
│   ├── config.py
│   ├── database.py
│   ├── graph.py
│   └── state.py
├── main.py
├── olist.db
├── README.md
├── requirements.txt
└── venv/

```


## 🗂 Project Components

### 1️⃣ `main.py`

Interactive CLI for users:

* Receives natural language questions.
* Initiates the LangGraph workflow.
* Displays structured output including SQL, raw data, and AI insights.

### 2️⃣ `src/database.py`

Handles database lifecycle:

* `init_database()`: Ingests CSVs from the `data/` folder into a SQLite `olist.db`.
* `execute_query()`: Standard interface for running SQL strings.

### 3️⃣ `src/config.py`

Centralized configuration for API keys (Gemini, Ollama, or Groq) and model parameters.

### 4️⃣ `src/state.py`

Defines the `AgentState` TypedDict used by LangGraph to pass the plan, messages, and data results between nodes.

### 5️⃣ `src/agents/sql_worker.py`

A specialized agent using a SQL toolkit to translate user intent into valid SQLite queries and retrieve the resulting dataset.

### 6️⃣ `src/agents/analyst_worker.py`

The qualitative engine: translates numbers into narratives, identifying trends, pain points, and strategic recommendations.

### 7️⃣ `src/agents/orchestrator.py`

The "brain" of the operation. It parses the user query and breaks it into a sequence of tasks for the specialized workers.

### 8️⃣ `src/graph.py`

The workflow engine built with **LangGraph**. It defines the state machine logic: Orchestrator ➔ SQL Worker ➔ Analyst Worker ➔ End.

---

## 🗄 Database Schema

| Table | Key Columns |
| --- | --- |
| **customers** | customer_id, city, state |
| **sellers** | seller_id, city, state |
| **products** | product_id, category_name, weight, photos_qty |
| **orders** | order_id, status, purchase_timestamp, delivery_dates |
| **order_items** | product_id, seller_id, price, freight_value |
| **order_payments** | payment_type, installments, payment_value |
| **order_reviews** | review_score, comment_message, creation_date |
| **geolocation** | zip_code, lat, lng, city, state |
| **translation** | category_name_portuguese, category_name_english |


## ⚡ Example Questions

* "What is the total number of orders by month in 2018?"
* "Which state has the highest concentration of customers?"
* "List the top 5 product categories by total revenue."
* "Is there a correlation between freight value and review scores?"
* "Show me the top 3 sellers by sales volume."

---

## 🏃 How to Run the Project

1. **Clone the repository**
```bash
git clone <repo_url>
cd olist-bi

```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate   # Windows

```


3. **Install dependencies**
```bash
pip install -r requirements.txt

```


4. **Initialize the database**
```bash
python src/database.py

```


5. **Run the BI system**
```bash
python main.py

```