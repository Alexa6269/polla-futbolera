import os
import pymysql
from flask import Flask

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        port=int(os.environ.get('DB_PORT')),
        ssl={'ssl_mode': 'REQUIRED'}
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Ejecuta el contenido de tu schema.sql
    with open('schema.sql', 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()

# Inicialización automática
try:
    init_db()
except Exception as e:
    print(f"La base de datos ya está inicializada o hubo un error: {e}")

@app.route('/')
def index():
    return "La Polla Futbolera está funcionando correctamente."