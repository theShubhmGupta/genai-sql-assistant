import os
from openai import OpenAI
from dotenv import load_dotenv  

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# 1. load_schema
# 2. load_prompt_template
# 3. validate_question
# 4. generate_sql
# 5. validate_sql
# 6. auto_fix_sql 
# 7. retry_with_error
# 8. run_safe_sql  
# 9. execute_sql
# 10. explain_result


import sqlite3
from pathlib import Path
import pandas as pd
import re

DB_PATH = Path("data/target.db")
CSV_DIR = Path("data/csv/") 



def initialize_database():
    
    if DB_PATH.exists():
        return  # DB already exists, do nothing

    print("Creating database from CSV files...")

    conn = sqlite3.connect(DB_PATH)

    for csv_file in CSV_DIR.glob("*.csv"):
        table_name = csv_file.stem
        df = pd.read_csv(csv_file)

        df.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )

        print(f"Loaded table: {table_name}")

    conn.close()
    print("Database creation complete.")



def load_schema():
    """
    Reads SQLite schema and returns it as text for the LLM
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, sql
        FROM sqlite_master
        WHERE type='table'
    """)

    schema_text = ""
    for table_name, table_sql in cursor.fetchall():
        schema_text += f"\n-- {table_name}\n{table_sql}\n"

    conn.close()
    return schema_text


def load_prompt_template():
    with open("prompts/sql_generator_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def validate_question(question: str):
    """
    Blocks destructive intent at the natural language level.
    Prevents silent fallbacks like SELECT *.
    """
    forbidden_intents = [
        "delete", "remove", "drop",
        "truncate", "update", "insert"
    ]

    q = question.lower()

    for word in forbidden_intents:
        if word in q:
            raise ValueError(
                "❌ This assistant is read-only. "
                "Destructive actions are not allowed."
            )


def generate_sql(prompt, schema, question):
    filled_prompt = prompt.format(
        schema=schema,
        question=question
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert SQL generator."},
            {"role": "user", "content": filled_prompt}
        ],
        temperature=0
    )

    sql = response.choices[0].message.content.strip()
    return sql

def generate_chat_title(question: str) -> str:
    """
    Generate a short ChatGPT-style conversation title.
    Used only for UI history (low cost, low risk).
    """

    prompt = f"""
Generate a short, descriptive conversation title (3–6 words).

Rules:
- No punctuation
- No emojis
- No filler words
- Abstract the intent
- Use Title Case
- Sound like a ChatGPT conversation title

Examples:
Question: How many orders were placed in each year?
Title: Yearly Order Trends

Question: Can we see monthly seasonality in 2018 summers?
Title: Summer Seasonality Analysis

Question:
{question}

Title:
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate concise analytics chat titles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=12
    )

    return response.choices[0].message.content.strip()


def validate_sql(sql: str):
    """
    Strict but safe SQL validator.
    Blocks destructive operations without false positives.
    """

    # Match only REAL SQL keywords (not substrings)
    forbidden_patterns = [
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bDROP\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bCREATE\b",
        r"\bREPLACE\b"
    ]

    sql_upper = sql.upper()

    # 1️. Block destructive operations
    for pattern in forbidden_patterns:
        if re.search(pattern, sql_upper):
            raise ValueError(
                f"❌ Forbidden SQL operation detected: {pattern.replace('\\b', '')}"
            )

    # 2️. Allow only SELECT / WITH queries
    if not sql_upper.strip().startswith(("SELECT", "WITH")):
        raise ValueError("❌ Only SELECT queries are allowed.")

    return True



def auto_fix_sql(sql: str) -> str:
    sql_upper = sql.upper()

    if "UNION" in sql_upper and "ORDER BY" in sql_upper:
        return f"""
        SELECT *
        FROM (
            {sql}
        ) AS union_result
        """
    return sql




def retry_with_error(prompt, schema, question, error):
    repair_prompt = f"""
You generated SQL that failed in SQLite.

ERROR:
{error}

Fix the SQL so it runs successfully in SQLite.
Follow all safety rules.
Return ONLY SQL.

Schema:
{schema}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert SQLite SQL fixer."},
            {"role": "user", "content": repair_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()



def run_safe_sql(prompt, schema, question, max_retries=1):

    # 1. Block destructive intent early
    validate_question(question)

    sql = generate_sql(prompt, schema, question)

    for attempt in range(max_retries + 1):
        try:
            # 2. Validate generated SQL
            validate_sql(sql)

            # 3. Auto-fix SQLite issues
            sql = auto_fix_sql(sql)

            # 4. Execute
            cols, rows = execute_sql(sql)

            return sql, cols, rows

        except Exception as e:
            if attempt >= max_retries:
                raise RuntimeError(f"Final SQL failed: {e}")

            # 5. Retry with error-aware fix
            sql = retry_with_error(
                prompt=prompt,
                schema=schema,
                question=question,
                error=str(e)
            )



def execute_sql(sql):
    if not sql.strip().lower().startswith(("select", "with")):
        raise ValueError("❌ Only SELECT queries can be executed")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        col_names = [d[0] for d in cursor.description] if cursor.description else []
    except Exception as e:
        conn.close()
        raise RuntimeError(f"SQL execution failed: {e}")

    conn.close()
    return col_names, rows



def explain_result(question, cols, rows):
    if not rows:
        return ["No data returned, so no insights can be generated."]

    preview_rows = rows[:10]

    result_text = "\n".join([str(row) for row in preview_rows])
    columns_text = ", ".join(cols)

    with open("prompts/sql_explainer_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    columns_text = ", ".join(cols)

    filled_prompt = prompt.format(
        question=question,
        columns=columns_text,
        result=result_text
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior business data analyst who explains insights clearly."},
            {"role": "user", "content": filled_prompt}
        ],
        temperature=0.3
    )

    explanation = response.choices[0].message.content.strip().split("\n")
    raw_points = explanation
    return normalize_explanation(raw_points)




def normalize_explanation(points: list[str]) -> dict:
    """
    Cleans LLM explanation output and separates insights & recommendations.
    Removes markdown, bullets, headings.
    """

    insights = []
    recommendations = []

    mode = "insight"

    for p in points:
        text = p.strip()

        # Detect section switches
        if "recommendation" in text.lower():
            mode = "recommendation"
            continue
        if "insight" in text.lower():
            mode = "insight"
            continue

        # Remove markdown symbols
        text = re.sub(r"^[-*•]+", "", text)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"#+", "", text)
        text = text.strip(" :")

        if not text:
            continue

        if mode == "insight":
            insights.append(text)
        else:
            recommendations.append(text)

    return {
        "insights": insights,
        "recommendations": recommendations
    }




def run():
    print("🤖 GenAI SQL Assistant Started\n")

    schema = load_schema()
    prompt = load_prompt_template()

    question = input("Ask your data question:\n")

    sql = generate_sql(prompt, schema, question)

    print("\n--- GENERATED SQL ---")
    print(sql)

    validate_sql(sql)

    cols, rows = execute_sql(sql)

    print("\n--- QUERY RESULT ---")
    print(" | ".join(cols))
    for row in rows:
        print(" | ".join(map(str, row)))


    explanation = explain_result(question, cols, rows)

    print("\n--- GENAI EXPLANATION ---")
    for point in explanation:
        print(f"• {point}")


if __name__ == "__main__":
    run()
