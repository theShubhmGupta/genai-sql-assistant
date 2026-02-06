
import streamlit as st
from src.genai_sql_engine import generate_chat_title


if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "active_query_id" not in st.session_state:
    st.session_state.active_query_id = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "new"

if "query_count" not in st.session_state:
    st.session_state.query_count = 0



# ---------------- Cost Guardrails ----------------
MAX_QUERIES_PER_SESSION = 5

# ---------------- Imports ----------------

from src.genai_sql_engine import (
    initialize_database,
    load_schema,
    load_prompt_template,
    generate_sql,
    execute_sql,
    explain_result,
    validate_sql
)

initialize_database()

# ---------------- Page setup ----------------
st.set_page_config(page_title="GenAI SQL Assistant", layout="wide")

st.title("GenAI SQL Assistant")
st.write("Ask questions in plain English. Get SQL, results, and insights.")




def render_explanation(explanation: dict):
    if not explanation:
        st.info("No explanation available.")
        return

    # ----------- KEY INSIGHTS -----------
    st.markdown(
        """
        <div style="
            font-size: 28px;
            font-weight: 600;
            margin-top: 28px;
            margin-bottom: 12px;
        ">
        💡Key Insights
        </div>
        """,
        unsafe_allow_html=True
    )

    for insight in explanation.get("insights", []):
        st.markdown(
            f"""
            <div style="
                background:#0f172a;
                border-left:4px solid #6366f1;
                padding:12px 14px;
                margin-bottom:10px;
                border-radius:8px;
                font-size:18px;
                line-height:1.6;
            ">
            {insight}
            </div>
            """,
            unsafe_allow_html=True
        )

    # ----------- RECOMMENDATIONS -----------
    st.markdown(
        """
        <div style="
            font-size: 28px;
            font-weight: 600;
            margin-top: 32px;
            margin-bottom: 12px;
        ">
        🎯 Recommendations
        </div>
        """,
        unsafe_allow_html=True
    )

    for rec in explanation.get("recommendations", []):
        st.markdown(
            f"""
            <div style="
                background:#020617;
                border-left:4px solid #22c55e;
                padding:12px 14px;
                margin-bottom:10px;
                border-radius:8px;
                font-size:18px;
                line-height:1.6;
            ">
            {rec}
            </div>
            """,
            unsafe_allow_html=True
        )




# ---------------- Query History Sidebar ----------------
st.sidebar.markdown("History")

for idx, item in enumerate(reversed(st.session_state.query_history)):
    real_idx = len(st.session_state.query_history) - idx - 1

    is_active = real_idx == st.session_state.active_query_id

    label = (
        f"▶️ {item['title']}" if is_active else f"   {item['title']}"
    )

    if st.sidebar.button(
        label,
        key=f"history_{real_idx}",
        use_container_width=True
    ):
        st.session_state.active_query_id = real_idx
        st.session_state.view_mode = "history"
        st.session_state.question_input = ""

        st.rerun()

# ---------------- Load resources ----------------
@st.cache_resource
def load_resources():
    schema = load_schema()
    prompt = load_prompt_template()
    return schema, prompt

schema, prompt = load_resources()

# ---------------- User input ----------------
question = st.text_input(
    "Ask your data question:",
    placeholder="e.g. How many orders were placed in each year?",
    key="question_input"
)

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "new"

active_item = None
if (
    st.session_state.view_mode == "history"
    and st.session_state.active_query_id is not None
):
    active_item = st.session_state.query_history[
        st.session_state.active_query_id
    ]


# ---------------- Run pipeline ----------------
if st.button("Run Query") and question:
    if st.session_state.query_count >= MAX_QUERIES_PER_SESSION:
        st.error("❌ Query limit reached for this session.")
        st.stop()

    st.session_state.query_count += 1

     # CLEAR old view
    st.session_state.view_mode = "new"
    st.session_state.active_query_id = None

    # 1️. Generate SQL
    with st.spinner("Generating SQL..."):
        sql = generate_sql(prompt, schema, question)

    st.subheader("🧾 Generated SQL")
    st.code(sql, language="sql")

    # 2️. Validate SQL
    try:
        validate_sql(sql)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # 3️. Execute SQL
    with st.spinner("Executing query..."):
        cols, rows = execute_sql(sql)

    # 4. Show query results
    st.subheader("📊 Query Result")

    if rows and cols:
        result_df = [{cols[i]: row[i] for i in range(len(cols))} for row in rows]
        st.dataframe(result_df)
    else:
        st.info("No results returned.")

    # 5. Generate explanation
    
    if rows:
        with st.spinner("Generating explanation..."):
            explanation = explain_result(question, cols, rows)

        render_explanation(explanation)

    else:
        st.info("No rows available for explanation.")
    
    # 6. Save Query History
    from datetime import datetime
 
    query_id = len(st.session_state.query_history)

    title = generate_chat_title(question)

    st.session_state.query_history.append({
        "id": query_id,
        "title": title,
        "question": question,
        "sql": sql,
        "columns": cols,
        "rows": rows,
        "explanation": explanation if rows else [],
        "time": datetime.now().strftime("%H:%M")
    })

        # Make this query active
    st.session_state.active_query_id = len(st.session_state.query_history) - 1


# ---------------- Render Active Query ----------------
if active_item:
    st.subheader("Question")
    st.markdown(f"{active_item['question']}")

    st.subheader("🧾 Generated SQL")
    st.code(active_item["sql"], language="sql")

    st.subheader("📊 Query Result")
    if active_item["rows"]:
        result_df = [
            {
                active_item["columns"][i]: row[i]
                for i in range(len(active_item["columns"]))
            }
            for row in active_item["rows"]
        ]
        st.dataframe(result_df)
    else:
        st.info("No results returned.")

    render_explanation(active_item["explanation"])

    
