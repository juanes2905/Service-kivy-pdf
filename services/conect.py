from flask import Flask, request, jsonify
import json
import logging
import pymssql
import os


from logging.handlers import TimedRotatingFileHandler
from password_utils import validatePassword

app = Flask(__name__)

def cargarSetting():
    settings_file = 'settings/Settings.json'
    default_settings = {
        "DATABASE": {
            "server": "127.0.0.1",
            "user": "user",
            "password": "User123",
            "database": "CI_ControlAccessDb"
        }
    }

    if not os.path.exists(settings_file):
        try:
            with open(settings_file, 'w') as f:
                json.dump(default_settings, f, indent=4)
                logging.info(f"WARNING: Creación del archivo exitosa {default_settings}")
            return default_settings['DATABASE']
        except Exception as e:
            raise RuntimeError(f'Error al crear el archivo de configuración: {str(e)}')
    
    try:
        with open(settings_file) as f:
            settings = json.load(f)
        return settings['DATABASE']
    except Exception as e:
        raise RuntimeError(f'Error al cargar la configuración de la base de datos: {str(e)}')

def connectDB():
    settings = cargarSetting()
    logging.info(settings)
    conn = pymssql.connect(server=settings['server'], user=settings['user'], password=settings['password'], database=settings['database'])

    cursor = conn.cursor(as_dict=True)
    logging.info("DATABASE: Conexion a la base de datos exitosa")
    return (conn, cursor)

@app.route('/query', methods=['GET'])
def buscaAqui():
    query = request.args.get('query')
    if not query:
        logging.error("DATABASE: Eror sin consulta")
        return jsonify({'ERROR': 'Sin consulta '}), 400
    
    try:
        conn, cursor = connectDB()
        # cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        logging.info("DATABASE: Conexion a la base de datos exitosa")
        conn.close()
        return jsonify({'result': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/donwloadUsers', method=['POST'])
def donwloaduserFile():
    pass


@app.route('/buscarUsuarios', methods=['POST'])
def buscar_usuarios():
    logging.info("<-FUNCION PARA BUSCAR A LOS USUARIOS->")
    buscar = request.json.get('busUsers')

    logging.info(f"Usuario: {buscar}")

    if not buscar:
        logging.warning("No se puede buscar el usuario sin el parámetro")
        return jsonify({'error': 'No se proporcionó ningún usuario para buscar'}), 400

    try:
        conn, cursor = connectDB()
        query = "SELECT * FROM New_People WHERE UserName LIKE %s "
        cursor.execute(query, ('%' + buscar + '%',))
        res = cursor.fetchone()  
        conn.close()

        if res:
            logging.info(res)
            return jsonify({'success': True, 'email': res['Email'], 'UserName': res['UserName'], 'password': res['StoredPassword']})
        else:
            logging.warning("DATABASE: No se encontró el usuario")
            return jsonify({'error': 'No se encontró el usuario'}), 404
    except Exception as e:
        logging.error(f"ERROR: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/login', methods=['POST'])
def login():
    logging.info("ENTRE A LA FUNCION LOGIN DE MI SERVICIO")

    email = request.json.get("email")
    password = request.json.get('password')

    logging.info(f"Usuario: {email}, password: {password}")
    
    try:
        conn, cursor = connectDB()
        query = "SELECT * FROM Tb_Users WHERE UserName = %s AND IsDelete = 0 AND IsActive  = 1"
        cursor.execute(query, (email))
        dataUser = cursor.fetchall()
        conn.close()

        logging.info(dataUser[0])
        if len(dataUser) > 0:
            dataUser = dataUser[0]
            if validatePassword(password, dataUser["StoredPassword"]):
                return jsonify({'success': True, 'email': dataUser['UserName'], 'password': dataUser['StoredPassword']}), 200
            else:
                return jsonify({'error': 'Correo usario o contraseña incorrectos'}), 401

        else:
            return jsonify({'error': 'Correo usario o contraseña incorrectos'}), 401
        
    except Exception as e:
        logging.error(f"ERROR: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/CreateUsers', methods=['POST'])
def CreateUsers():
    logging.info("<-FUNCION PARA LA CREACION DE USARIOS->")
    email = request.form.get('email')
    user = request.form.get('user')
    password = request.form.get('password')
    
    if not (email and user and password):
        
        logging.warning("SEARCH: No se puede insertar usuario sin los registros")
        return jsonify({'ERROR': 'Faltan campos por validar'}), 400
    
    try:
        conn, cursor = connectDB()
        query = "INSERT INTO New_People (Email, UserName, StoredPassword) VALUES (%s, %s, %s)"
        cursor.execute(query, (email, user, password))
        conn.commit()  
        inser = cursor.lastrowid  
        conn.close()

        if inser:
            
            logging.info("Usuario insertado correctamente en la base de datos. ID: %d", inser)
            return jsonify({'success': True, 'id': inser}), 200
        else:
            
            logging.error("No se pudo obtener el ID del usuario insertado.")
            return jsonify({'ERROR': 'No se pudo obtener el ID del usuario insertado.'}), 500
    except Exception as error:
        
        logging.error("Error durante la inserción en la base de datos: %s", str(error))
        return jsonify({'error': str(error)}), 500


        
if __name__ == '__main__':
    logsFolder = "logs"
    os.makedirs(logsFolder, exist_ok=True)
    logging.basicConfig(
        level       = logging.INFO,
        format      = "%(asctime)s [%(levelname)s]    %(module)s:%(lineno)d    %(funcName)s    | %(message)s" ,
        datefmt     = '%Y-%m-%d %H:%M:%S',
        handlers    = [TimedRotatingFileHandler(logsFolder + "/logs.log", when    = "d", interval    = 1, backupCount    = 3), logging.StreamHandler()]
        )
    app.run(debug=True, port=8000, host='0.0.0.0')