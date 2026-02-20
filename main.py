import time
from src.graph import app
from src.logger import log_interaction

def main():
    print("\n🚀 Olist Multi-Agent BI System\n")

    while True:
        question = input("Ask a question about Olist (type 'exit' to quit): ").strip()

        if question.lower() == "exit":
            print("\n👋 Exiting... Goodbye!\n")
            break

        if not question:
            print("⚠️ Please enter a valid question.\n")
            continue

        try:
            start_time = time.time()

            # Invoke LangGraph app
            state = app.invoke({"question": question})

            execution_time = round(time.time() - start_time, 2)

            # Extract safely
            sql_query = state.get("sql_query", "N/A")
            db_result = state.get("db_result", {})
            analysis = state.get("analysis", "No response generated.")

            # Extract numeric result if possible
            numeric_output = ""
            if db_result.get("rows") and db_result.get("columns"):
                if len(db_result["rows"][0]) == 1:
                    numeric_value = db_result["rows"][0][0]
                    numeric_output = f"**Numeric Result:** {numeric_value}\n"

            # Display outputs
            print("\n🧠 Generated SQL:\n")
            print(sql_query)

            print("\n📊 Running Analysis...\n✅ Done.\n")

            if numeric_output:
                print(numeric_output)

            print("📄 FINAL ANSWER:\n")
            print(analysis)

            print(f"\n⏱ Execution Time: {execution_time} seconds\n")

            # 🔥 Log interaction
            log_interaction(
                question=question,
                sql_query=sql_query,
                db_result=db_result,
                final_answer=analysis
            )

        except Exception as e:
            print(f"\n❌ System Error: {str(e)}\n")


if __name__ == "__main__":
    main()