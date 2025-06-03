import os
import re
from dotenv import load_dotenv

load_dotenv()

import openai
import mysql.connector
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

class QueryRequest(BaseModel):
    question: str

def get_db_schema():
    cnx = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = cnx.cursor()

    # Tablas y columnas
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    schema = {}
    for table in tables:
        cursor.execute(f"SHOW FULL COLUMNS FROM `{table}`")
        columns = []
        for row in cursor.fetchall():
            columns.append({"name": row[0], "type": row[1], "comment": row[8]})
        schema[table] = columns

    # Claves foráneas y relaciones
    cursor.execute(f"""
    SELECT 
        TABLE_NAME, COLUMN_NAME, 
        REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = '{MYSQL_DB}' AND REFERENCED_TABLE_NAME IS NOT NULL
    """)
    relations = []
    for t, col, rt, rc in cursor.fetchall():
        relations.append((t, col, rt, rc))

    cursor.close()
    cnx.close()

    # Esquema legible para el LLM
    schema_txt = "Esquema de la base de datos:\n"
    for table, cols in schema.items():
        schema_txt += f"- Tabla `{table}` con columnas: " + ", ".join(
            [f"`{c['name']}` ({c['type']})" for c in cols]) + ".\n"
    if relations:
        schema_txt += "Relaciones:\n"
        for t, col, rt, rc in relations:
            schema_txt += (
                f"- `{t}`.`{col}` referencia `{rt}`.`{rc}`.\n"
            )
    return schema_txt

def ask_llm(question, schema_description):
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un experto en SQL y bases de datos relacionales. "
                "Tu tarea es convertir preguntas en lenguaje natural a consultas SQL para MySQL, "
                "aprovechando el esquema y las relaciones proporcionadas. "
                "Si la consulta requiere información de varias tablas relacionadas, utiliza los JOIN apropiados "
                "y selecciona los campos más descriptivos (ejemplo: username, product name, etc). "
                "Solo responde con el código SQL, sin escribir 'sql', 'SQL:', 'Query:' o ningún prefijo antes del SELECT, ni comentarios extra.\n"
                + schema_description
            )
        },
        {"role": "user", "content": question}
    ]
    response = client.chat.completions.create(
        model="gpt-4.1",  # Cambia si usas otro modelo
        messages=messages,
        max_tokens=256,
        temperature=0,
    )
    return response.choices[0].message.content.strip()

def clean_sql(sql):
    """
    Elimina cualquier prefijo como 'sql', 'SQL:', 'Query:' al inicio de la consulta.
    """
    sql = sql.strip()
    # Elimina posibles prefijos (con o sin dos puntos)
    sql = re.sub(r"^(sql\s*|SQL\s*:|Query\s*:)\s*", "", sql, flags=re.IGNORECASE)
    return sql

def execute_sql(sql):
    cnx = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = cnx.cursor()
    cursor.execute(sql)
    try:
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    except Exception:
        result = []
        columns = []
    cursor.close()
    cnx.close()
    return {"columns": columns, "rows": result}

@app.post("/mcp/query")
def mcp_query(request: QueryRequest):
    schema_description = get_db_schema()
    sql = ask_llm(request.question, schema_description)
    sql = clean_sql(sql)  # <-- LIMPIA EL SQL ANTES DE EJECUTAR
    try:
        result = execute_sql(sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error ejecutando SQL: {e}\nConsulta generada: {sql}")
    return {"sql": sql, "result": result}