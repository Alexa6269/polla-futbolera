from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import random

app = Flask(__name__)
app.secret_key = "polla_futbolera_secret_key_123"

# Configuración ajustada a tu phpMyAdmin en Mac
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       
    'password': '',       # Si usas MAMP y no conecta, prueba cambiando '' por 'root'
    'database': 'polla',  # Nombre exacto de tu base de datos en la captura
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME'),
        port=int(os.environ.get('DB_PORT')),
        ssl={'ssl_mode': 'REQUIRED'}
    )

# ARRAY 1: Las 10 superpotencias con mayor probabilidad de ganar el Mundial 2026
EQUIPOS_PRO = [
    "Francia", "Brasil", "Inglaterra", "Argentina", "España", 
    "Alemania", "Portugal", "Países Bajos", "Bélgica", "Croacia"
]

# ARRAY 2: Los siguientes 10 equipos fuertes, pero con probabilidad un poco menor
EQUIPOS_SECUNDARIOS = [
    "Turquia", "Colombia", "Uruguay", "Marruecos", "Estados Unidos", 
    "México", "Japón", "Noruega", "Dinamarca", "Suiza"
]

@app.route('/')
def index():
    # Obtener el histórico de asignaciones para la tabla
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre_usuario, equipo_pro, equipo_secundario, fecha_registro FROM asignaciones ORDER BY fecha_registro DESC")
            historial = cursor.fetchall()
            
            # Contar cuántos cupos quedan
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
            # 1. Validar si el usuario ya existe
            cursor.execute("SELECT id FROM asignaciones WHERE nombre_usuario = %s", (nombre,))
            if cursor.fetchone():
                flash(f"El usuario '{nombre}' ya está registrado en la polla.", "error")
                return redirect(url_for('index'))
            
            # 2. Validar disponibilidad de cupos y obtener equipos ya asignados
            cursor.execute("SELECT equipo_pro, equipo_secundario FROM asignaciones")
            asignados = cursor.fetchall()
            
            if len(asignados) >= 10:
                flash("¡Lo sentimos! Ya se agotaron los 10 cupos disponibles para el sorteo.", "error")
                return redirect(url_for('index'))
            
            # Listas de equipos ya ocupados en la BD
            pros_ocupados = [row['equipo_pro'] for row in asignados]
            secs_ocupados = [row['equipo_secundario'] for row in asignados]
            
            # 3. Filtrar equipos disponibles (Regla de Oro)
            pros_disponibles = [e for e in EQUIPOS_PRO if e not in pros_ocupados]
            secs_disponibles = [e for e in EQUIPOS_SECUNDARIOS if e not in secs_ocupados]
            
            # 4. Sorteo aleatorio
            pro_elegido = random.choice(pros_disponibles)
            sec_elegido = random.choice(secs_disponibles)
            
            # 5. Guardar en la Base de Datos
            sql = "INSERT INTO asignaciones (nombre_usuario, equipo_pro, equipo_secundario) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nombre, pro_elegido, sec_elegido))
            conn.commit()
            
            # Preparar resultado para la pantalla de éxito
            resultado = {
                'usuario': nombre,
                'pro': pro_elegido,
                'secundario': sec_elegido
            }
            
            # Recargar el historial actualizado para renderizar la página de nuevo
            cursor.execute("SELECT nombre_usuario, equipo_pro, equipo_secundario, fecha_registro FROM asignaciones ORDER BY fecha_registro DESC")
            historial = cursor.fetchall()
            cupos_disponibles = 10 - len(historial)
            
            return render_template('index.html', historial=historial, cupos=cupos_disponibles, resultado=resultado)
            
    except Exception as e:
        flash(f"Ocurrió un error en el sistema: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)