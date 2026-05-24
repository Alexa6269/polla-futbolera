import os
import pymysql
import random
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "polla_futbolera_secret_key_123"

# Conexión adaptada a Render/Aiven usando variables de entorno
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        port=int(os.environ.get('DB_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={'ssl_mode': 'REQUIRED'}
    )

EQUIPOS_PRO = ["Francia", "Brasil", "Inglaterra", "Argentina", "España", "Alemania", "Portugal", "Países Bajos", "Italia", "Uruguay"]
EQUIPOS_SECUNDARIOS = ["Bélgica", "Colombia", "Croacia", "Marruecos", "Estados Unidos", "México", "Japón", "Senegal", "Dinamarca", "Suiza"]

@app.route('/')
def index():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre_usuario, equipo_pro, equipo_secundario, fecha_registro FROM asignaciones ORDER BY fecha_registro DESC")
            historial = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) as total FROM asignaciones")
            total_asignados = cursor.fetchone()['total']
            cupos_disponibles = 10 - total_asignados
    finally:
        conn.close()
    return render_template('index.html', historial=historial, cupos=cupos_disponibles)

@app.route('/procesar', methods=['POST'])
def procesar():
    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        flash("El nombre no puede estar vacío.", "error")
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM asignaciones WHERE nombre_usuario = %s", (nombre,))
            if cursor.fetchone():
                flash(f"El usuario '{nombre}' ya está registrado.", "error")
                return redirect(url_for('index'))
            
            cursor.execute("SELECT equipo_pro, equipo_secundario FROM asignaciones")
            asignados = cursor.fetchall()
            
            if len(asignados) >= 10:
                flash("¡Ya se agotaron los 10 cupos!", "error")
                return redirect(url_for('index'))
            
            pros_ocupados = [row['equipo_pro'] for row in asignados]
            secs_ocupados = [row['equipo_secundario'] for row in asignados]
            
            pros_disponibles = [e for e in EQUIPOS_PRO if e not in pros_ocupados]
            secs_disponibles = [e for e in EQUIPOS_SECUNDARIOS if e not in secs_ocupados]
            
            pro_elegido = random.choice(pros_disponibles)
            sec_elegido = random.choice(secs_disponibles)
            
            cursor.execute("INSERT INTO asignaciones (nombre_usuario, equipo_pro, equipo_secundario) VALUES (%s, %s, %s)", (nombre, pro_elegido, sec_elegido))
            conn.commit()
            
            resultado = {'usuario': nombre, 'pro': pro_elegido, 'secundario': sec_elegido}
            
            cursor.execute("SELECT nombre_usuario, equipo_pro, equipo_secundario, fecha_registro FROM asignaciones ORDER BY fecha_registro DESC")
            historial = cursor.fetchall()
            return render_template('index.html', historial=historial, cupos=10 - len(historial), resultado=resultado)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()