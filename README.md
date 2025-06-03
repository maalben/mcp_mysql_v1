# MCP Server: Natural Language to SQL (MySQL)

Implementa un servidor MCP que recibe instrucciones en lenguaje natural, las traduce a SQL usando un modelo de lenguaje (como OpenAI GPT), y ejecuta las consultas sobre una base de datos MySQL. Los resultados se presentan al usuario a través de una interfaz web simple (Streamlit).

---

## 🚀 Requisitos

- Python 3.8+
- Dependencias:
  - fastapi
  - uvicorn
  - streamlit
  - openai
  - mysql-connector-python
  - python-dotenv

Instala todas las dependencias con:
pip install -r requirements.txt

---

## 🧪 Uso de entorno virtual (recomendado)

1. Crea un entorno virtual:

En Linux/macOS:
python3 -m venv venv  
source venv/bin/activate

En Windows:
python -m venv venv  
venv\\Scripts\\activate

2. Instala las dependencias dentro del entorno:
pip install -r requirements.txt

3. Cuando termines, puedes salir del entorno con:
deactivate

---

## 🚮 ¿Cómo eliminar el entorno virtual?

1. Desactiva el entorno virtual si está activo:
deactivate

2. Elimina la carpeta del entorno virtual llamada "venv":

En Linux/macOS:
rm -rf venv

En Windows (CMD o PowerShell):
rmdir /s /q venv

Y borrar la carpeta de pycache
rm -rf __pycache__


O simplemente bórrala desde el explorador de archivos.

---

## 📁 Estructura de Archivos

- mcp_server.py → Servidor FastAPI para procesar instrucciones en lenguaje natural y ejecutar consultas SQL.
- app.py → Interfaz web con Streamlit para interactuar con el usuario.
- requirements.txt → Lista de dependencias.
- .env.example → Ejemplo de variables de entorno necesarias.
- README.md → Este archivo.

---

## 📐 Arquitectura

             HTTP POST
┌───────────────┐      ┌────────────────────┐
│               │─────►│                    │
│   Interfaz    │      │     MCP Server     │
│  Web (Usuario)│◄─────│    (FastAPI App)   │
│  (Streamlit)  │      │                    │
└───────────────┘      └────────────────────┘
       │                        │
       ▼                        ▼
Usuario escribe        1. Recibe petición / pregunta
pregunta en NL         2. Envía prompt al LLM (API o local)
                              │
                   ┌────────────────────────────┐
                   │      LLM (Modelo IA)       │
                   │ (GPT, Ollama, etc.)        │
                   └────────────────────────────┘
                              │
                              ▼
                   3. LLM responde con SQL
                              │
                              ▼
                   4. Ejecuta SQL en MySQL
                   ┌────────────────────────────┐
                   │      MySQL Database        │
                   └────────────────────────────┘
                              │
                              ▼
                   5. Devuelve resultados
                   6. API envía respuesta a UI
       ▲                        ▲
       │                        │
       └──── Visualiza resultado┘
       
---

## ⚙️ ¿Cómo usar?

1. Copia el archivo .env.example a .env y configura tus credenciales de MySQL y la API Key de OpenAI.
2. Inicia el backend:
   uvicorn mcp_server:app --reload --port 8001
3. Inicia la interfaz web:
   streamlit run app.py
4. Escribe tus consultas en lenguaje natural en la interfaz. El sistema generará la consulta SQL y mostrará los resultados en pantalla.

---

## 🌱 Ejemplo de .env.example

OPENAI_API_KEY=tu_api_key  
MYSQL_HOST=localhost  
MYSQL_USER=usuario  
MYSQL_PASSWORD=tu_password  
MYSQL_DB=nombre_bd

---

## 👀 Ejemplo de uso

- Usuario ingresa: "Muéstrame los usuarios registrados esta semana"
- El sistema genera SQL:  
  SELECT * FROM users WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);
- El resultado de la consulta se muestra en la interfaz Streamlit.

---

## 🚨 Buenas prácticas y recomendaciones

- No uses este sistema en bases de datos productivas sin revisión humana del SQL generado.
- Se recomienda limitar las operaciones a solo lectura (SELECT) para evitar cambios no deseados.
- Protege tus credenciales y variables de entorno. No subas tu archivo .env al repositorio.
- Puedes añadir validadores para aceptar únicamente consultas seguras.

---

## 📚 Licencia y aportes

¡Usa, adapta y mejora este proyecto! Si tienes sugerencias o problemas, crea un issue o envía un pull request.

---