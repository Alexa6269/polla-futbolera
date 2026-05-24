import os
import pymysql
from flask import Flask, render_template

app = Flask(__name__)

# Configuración de conexión usando las variables de entorno de Render
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        port=int(os.environ.get('DB_PORT')),
        ssl={'ssl_mode': 'REQUIRED'}
    )

# Asegura que la tabla exista al arrancar
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    with open('schema.sql', 'r') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()

# Inicialización automática
try:
    init_db()
except Exception as e:
    print(f"La base de datos está lista o ya existía: {e}")

# Ruta principal que muestra tu index.html
@app.route('/')
def index():
    # Aquí puedes agregar la lógica para traer datos de 'asignaciones' si lo necesitas
    return render_template('index.html', cupos=0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))