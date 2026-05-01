from flask import Flask, render_template, request, redirect, url_for, session, jsonify 
import pymssql 
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Filtro personalizado para formatear números como moneda
@app.template_filter('currency_format')
def format_currency(value):
    try:
        num = float(value)
        # Formatea con 2 decimales
        formatted = f"{num:.2f}"
        # Divide en parte entera y decimal
        parts = formatted.split('.')
        integer_part = parts[0]
        decimal_part = parts[1]
        
        # Agrega separador de miles (coma) a la parte entera
        formatted_integer = ''
        for i, char in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                formatted_integer = ',' + formatted_integer
            formatted_integer = char + formatted_integer
        
        return f"{formatted_integer}.{decimal_part}"
    except:
        return "0.00"

# Filtro personalizado para formatear fechas para input date
@app.template_filter('date_input')
def format_date_input(value):
    if not value:
        return ''
    try:
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        elif isinstance(value, str):
            return value
        else:
            return ''
    except:
        return ''

DB_CONFIG = {
    'server': 'h7dxy4lo9g.database.windows.net',
    'database': 'dbformularios',
    'username': 'serviciospropeep',
    'password': 'servicios2024@'
}

def get_conn():
    return pymssql.connect(
        server=DB_CONFIG['server'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password']
    )

def get_cursor(conn):
    return conn.cursor(as_dict=True)

# ─────────────────────────── AUTH ───────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cedula = request.form.get('cedula', '').strip()
        clave  = request.form.get('clave', '').strip()
        try:
            conn = get_conn()
            cur  = get_cursor(conn)
            cur.execute(
                "SELECT documento, nombres, ctabanco,'activo' as Estatus FROM dbo.ConsultaNomina "
                "WHERE documento = %s AND ctabanco = %s",
                (cedula, clave)
            )
            row = cur.fetchone()
            if not row:
                error = "Cédula o clave incorrecta. Verifique sus datos."
            elif str(row['Estatus']).strip() in ('0', 'Inactivo', 'inactivo', 'N', 'False', 'false'):
                error = "Su usuario está inactivo. Comuníquese con Recursos Humanos."
            else:
                session['cedula']  = row['documento']
                session['nombre']  = row['nombres']
                conn.close()
                return redirect(url_for('menu'))
            conn.close()
        except Exception as e:
            error = f"Error de conexión: {str(e)}"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────── MENU ───────────────────────────

@app.route('/menu')
def menu():
    if 'cedula' not in session:
        return redirect(url_for('login'))
    cedula = session['cedula']
    depto  = ''
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        cur.execute("SELECT DEPTO FROM dbo.ConsultaNomina WHERE documento = %s", (cedula,))
        row = cur.fetchone()
        if row:
            depto = row['DEPTO'] or ''
        conn.close()
    except Exception:
        pass
    return render_template('menu.html', nombre=session.get('nombre',''), depto=depto)

# ─────────────────────────── DATOS EMPLEADO ─────────────────

@app.route('/formulario', methods=['GET'])
def formulario():
    if 'cedula' not in session:
        return redirect(url_for('login'))
    cedula = session['cedula']
    empleado = {}
    familiares = []
    academicos = []
    nomina = {}
    id_emp = None

    try:
        conn = get_conn()
        cur  = get_cursor(conn)

        # Nomina (read-only fields)
        cur.execute(
            "SELECT nombres, funcion, DEPTO, Sexo FROM dbo.ConsultaNomina WHERE documento = %s",
            (cedula,)
        )
        n = cur.fetchone()
        if n:
            nomina = {'nombres': n['nombres'], 'funcion': n['funcion'], 'DEPTO': n['DEPTO'], 'Sexo': n['Sexo']}

        # DatosEmpleado
        cur.execute("SELECT * FROM rrhh.DatosEmpleados WHERE Cedula = %s", (cedula,))
        row  = cur.fetchone()
        if row:
            empleado = row
            id_emp   = empleado.get('Id')

            # Familiares
            cur.execute("SELECT * FROM rrhh.DatosFamiliares WHERE IdDatosEmpleado = %s", (id_emp,))
            familiares = cur.fetchall()

            # Academicos
            cur.execute("SELECT * FROM rrhh.DatosAcademicos WHERE IdDatosEmpleado = %s", (id_emp,))
            academicos = cur.fetchall()

        conn.close()
    except Exception as e:
        return render_template('formulario.html', error=str(e), empleado={},
                               familiares=[], academicos=[], nomina=nomina, id_emp=None)

    return render_template('formulario.html', empleado=empleado, familiares=familiares,
                           academicos=academicos, nomina=nomina, id_emp=id_emp, error=None)

@app.route('/empleado/guardar', methods=['POST'])
def empleado_guardar():
    if 'cedula' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401
    cedula = session['cedula']
    d = request.json
    now  = datetime.now()
    user = cedula
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        cur.execute("SELECT Id FROM rrhh.DatosEmpleados WHERE Cedula = %s", (cedula,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE rrhh.DatosEmpleados SET
                    EstadoCivil=%s, TelefonoMovil=%s, TelefonoFijo=%s, TelefonoFlota=%s,
                    ContactoEmergencia=%s, TelefonoEmergencia=%s,
                    NivelAcademico=%s, ProfesionOficio=%s,
                    Provincia=%s, Municipio=%s, Direccion=%s, Sector=%s,
                    FechaNacimiento=%s, Email=%s, EmailPersonal=%s, Supervisor=%s,
                    ModificadoPor=%s, FechaModificado=%s
                WHERE Cedula=%s
            """, (
                d.get('EstadoCivil'), d.get('TelefonoMovil'), d.get('TelefonoFijo'),
                d.get('TelefonoFlota'), d.get('ContactoEmergencia'), d.get('TelefonoEmergencia'),
                d.get('NivelAcademico'), d.get('ProfesionOficio'),
                d.get('Provincia'), d.get('Municipio'), d.get('Direccion'), d.get('Sector'),
                d.get('FechaNacimiento') or None, d.get('Email'), d.get('EmailPersonal'), d.get('Supervisor'),
                user, now, cedula
            ))
            cur.execute("SELECT Id FROM rrhh.DatosEmpleados WHERE Cedula = %s", (cedula,))
            row_id = cur.fetchone()
            id_emp = row_id['Id'] if row_id else None
        else:
            # Get nombre/sexo from nomina
            cur.execute("SELECT nombres, Sexo, funcion, DEPTO FROM dbo.ConsultaNomina WHERE documento=%s", (cedula,))
            n = cur.fetchone()
            nombre = n['nombres'] if n else ''
            sexo   = n['Sexo'] if n else ''
            cargo  = n['funcion'] if n else ''
            depto  = n['DEPTO'] if n else ''
            cur.execute("""
                INSERT INTO rrhh.DatosEmpleados
                    (Cedula, Nombre, Sexo, EstadoCivil, TelefonoMovil, TelefonoFijo, TelefonoFlota,
                     ContactoEmergencia, TelefonoEmergencia, Departamento, Cargo,
                     NivelAcademico, ProfesionOficio,
                     Provincia, Municipio, Direccion, Sector, FechaNacimiento, Email, EmailPersonal, Supervisor, Estatus,
                     FechaRegistro, RegistradoPor, FechaModificado)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s,%s)
            """, (
                cedula, nombre, sexo,
                d.get('EstadoCivil'), d.get('TelefonoMovil'), d.get('TelefonoFijo'),
                d.get('TelefonoFlota'), d.get('ContactoEmergencia'), d.get('TelefonoEmergencia'),
                depto, cargo,
                d.get('NivelAcademico'), d.get('ProfesionOficio'),
                d.get('Provincia'), d.get('Municipio'), d.get('Direccion'), d.get('Sector'),
                d.get('FechaNacimiento') or None, d.get('Email'), d.get('EmailPersonal'), d.get('Supervisor'),
                now, user, now
            ))
            cur.execute("SELECT Id FROM rrhh.DatosEmpleados WHERE Cedula = %s", (cedula,))
            row_id = cur.fetchone()
            id_emp = row_id['Id'] if row_id else None

        conn.commit()
        conn.close()
        return jsonify({'ok': True, 'id_emp': id_emp})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})

# ─────────────────────────── FAMILIARES ─────────────────────

@app.route('/familiar/guardar', methods=['POST'])
def familiar_guardar():
    if 'cedula' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401
    d = request.json
    now = datetime.now()
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        if d.get('Id'):
            cur.execute("""
                UPDATE rrhh.DatosFamiliares SET
                    Cedula=%s, Nombre=%s, Sexo=%s, FechaNacimiento=%s, Edad=%s,
                    Parentesco=%s, Estudia=%s, TipoEstudio=%s,
                    ModificadoPor=%s, FechaModificado=%s
                WHERE Id=%s
            """, (
                d.get('Cedula'), d.get('Nombre'), d.get('Sexo'),
                d.get('FechaNacimiento') or None,
                d.get('Edad') or None,
                d.get('Parentesco'), 1 if d.get('Estudia') else 0,
                d.get('TipoEstudio'), session['cedula'], now, d['Id']
            ))
        else:
            cur.execute("""
                INSERT INTO rrhh.DatosFamiliares
                    (IdDatosEmpleado, Cedula, Nombre, Sexo, FechaNacimiento, Edad,
                     Parentesco, Estudia, TipoEstudio,
                     FechaRegistro, RegistradoPor, FechaModificado)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                d.get('IdDatosEmpleado'),
                d.get('Cedula'), d.get('Nombre'), d.get('Sexo'),
                d.get('FechaNacimiento') or None,
                d.get('Edad') or None,
                d.get('Parentesco'), 1 if d.get('Estudia') else 0,
                d.get('TipoEstudio'), now, session['cedula'], now
            ))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})

@app.route('/familiar/eliminar/<int:fid>', methods=['DELETE'])
def familiar_eliminar(fid):
    if 'cedula' not in session:
        return jsonify({'ok': False}), 401
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        cur.execute("DELETE FROM rrhh.DatosFamiliares WHERE Id = %s", (fid,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})

# ─────────────────────────── ACADÉMICOS ─────────────────────

@app.route('/academico/guardar', methods=['POST'])
def academico_guardar():
    if 'cedula' not in session:
        return jsonify({'ok': False, 'msg': 'No autenticado'}), 401
    d   = request.json
    now = datetime.now()
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        if d.get('Id'):
            cur.execute("""
                UPDATE rrhh.DatosAcademicos SET
                    Titulo=%s, Institucion=%s, Fecha=%s,
                    ModificadoPor=%s, FechaModificado=%s
                WHERE Id=%s
            """, (
                d.get('Titulo'), d.get('Institucion'),
                d.get('Fecha') or None,
                session['cedula'], now, d['Id']
            ))
        else:
            cur.execute("""
                INSERT INTO rrhh.DatosAcademicos
                    (IdDatosEmpleado, Titulo, Institucion, Fecha,
                     FechaRegistro, RegistradoPor, FechaModificado)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                d.get('IdDatosEmpleado'),
                d.get('Titulo'), d.get('Institucion'),
                d.get('Fecha') or None,
                now, session['cedula'], now
            ))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})

@app.route('/academico/eliminar/<int:aid>', methods=['DELETE'])
def academico_eliminar(aid):
    if 'cedula' not in session:
        return jsonify({'ok': False}), 401
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        cur.execute("DELETE FROM rrhh.DatosAcademicos WHERE Id = %s", (aid,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})

# ─────────────────────────── VOLANTE DE PAGO ─────────────────

@app.route('/volantepago')
def volantepago():
    if 'cedula' not in session:
        return redirect(url_for('login'))
    cedula = session['cedula']
    empleado = {}
    try:
        conn = get_conn()
        cur  = get_cursor(conn)
        cur.execute("SELECT * FROM dbo.consultanomina WHERE documento = %s", (cedula,))
        row  = cur.fetchone()
        if row:
            empleado = row
        conn.close()
    except Exception as e:
        empleado = {'error': str(e)}
    return render_template('volantepago.html', empleado=empleado, cedula=cedula)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")
