from flask import Blueprint, request, send_file
from modelos import EstadoArchivosSchema, Users, UsersSchema
import os
from utils import FileUtils
from repository.UserRepository import UserRepository
from celery import Celery
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_current_user, get_jwt, get_jwt_identity
from flask import jsonify

controllers = Blueprint('controllers', __name__)

estado_archivo_schema = EstadoArchivosSchema()
users_schema = UsersSchema()
fileUtils = FileUtils()
userRepository = UserRepository()

celery_app = Celery('tasks', broker='redis://10.138.0.3:6379/0')


@celery_app.task(name='conversor')
def obtener_id_proceso(id):
    pass


@controllers.route('/auth/signup', methods=['POST'])
def registrar_usuario():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')

    if not email or not username or not password1 or not password2:
        return 'Los campos email, username y password son requeridos', 400

    if password1 != password2:
        return 'Las contraseñas deben ser iguales', 400
    else:
        if not fileUtils.validar_contrasena(password1):
            return 'La contraseña debe tener mínimo 8 caracteres, al menos una mayúscula, al menos una minúscula y símbolos (!@#$%^&*)', 400

    stored_email = userRepository.obtener_por_email(email)

    if stored_email:

        return 'El email ya se encuentra en uso'
    else:
        if not fileUtils.validar_email(email):
            return 'Formato de email incorrecto'

    stored_username = userRepository.obtener_por_username(username)

    if stored_username:
        return 'El nombre de usuario ya se encuentra en uso'

    user = Users(
        username=username,
        email=email,
        password=generate_password_hash(password1)
    )

    userRepository.guardar_usuario(user)
    return users_schema.dump(user)


@controllers.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return 'Usuario y contraseña son obligatorios', 400

    stored_user = userRepository.obtener_por_username(username)
    if stored_user:
        if not check_password_hash(stored_user.password, password):
            return 'Credenciales incorrectas', 401
    else:
        return 'Credenciales incorrectas', 401
    token_de_acceso = create_access_token(identity=stored_user.id)
    return jsonify({"mensaje": "Inicio de sesión exitoso", "__token": token_de_acceso, "id": stored_user.id})


@controllers.route('/tasks', methods=['POST'])
@jwt_required()
def procesar_archivo():
    user_id = get_jwt_identity()
    archivo = request.files['fileName']
    extension_convertir = request.form.get('newFormat')

    if archivo:
        nombre_del_archivo = archivo.filename
        extension_original = nombre_del_archivo.split('.')[-1]

        extension_original_minuscula = extension_original.lower()
        extension_convertir_minuscula = extension_convertir.lower()

        mensaje = fileUtils.validar_request(extension_original_minuscula, extension_convertir_minuscula)
        if mensaje == '':

            estado_archivo = fileUtils.crear_estado_documento(nombre_del_archivo, 'Ingresado',
                                                              extension_original_minuscula,
                                                              extension_convertir_minuscula, user_id)
            fileUtils.guardar_archivo_original(archivo, estado_archivo.id)
            fileUtils.editar_nombre_documento(estado_archivo.id, f"{estado_archivo.id}_{archivo.filename}")

            mensaje = {"id": estado_archivo.id}
            args = (estado_archivo.id,)
            #obtener_id_proceso.apply_async(args)
            fileUtils.pub(args)
        else:
            return mensaje, 400
    else:
        return "Debe enviar un archivo en el campo fileName", 400

    return estado_archivo_schema.dump(estado_archivo)


@controllers.route('/tasks/<int:id>', methods=['GET'])
@jwt_required()
def encontrar_archivo(id):
    user_id = get_jwt_identity()
    estado = fileUtils.obtener_estado_tareas_por_id(id, user_id)
    if estado:
        #url_archivo_original = f"http://{request.host}/api/files/original/{estado.nombre_archivo}"
        url_archivo_original = fileUtils.descargar_video('original', estado.nombre_archivo)
        if estado.nuevo_archivo:
            #url_archivo_convertido = f"http://{request.host}/api/files/convertido/{estado.nuevo_archivo}"
            url_archivo_convertido = fileUtils.descargar_video('convertido', estado.nuevo_archivo)
        else:
            url_archivo_convertido = ''
        return {"tarea": estado_archivo_schema.dump(estado), "url archivo original": url_archivo_original,
                "url_archivo_convertido": url_archivo_convertido}
    else:
        return "Archivo no encontrado", 404


@controllers.route('/files/<string:tipo>/<string:nombre>', methods=['GET'])
@jwt_required()
def obtener_archivo_descargar(tipo, nombre):
    if tipo == 'original' or tipo == 'convertido':
        user_id = get_jwt_identity()
        estado = fileUtils.obtener_estado_tareas_por_estado_y_nuevo_archivo(user_id, tipo, nombre)
        if estado:
            url_firmada = fileUtils.descargar_video(tipo, nombre)
            if tipo == 'original':
                formato_video = estado.extension_original
                titulo = 'Video original'
            else:
                formato_video = estado.extension_nueva
                titulo = 'Video convertido'
            return f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Ver Video</title>
                    </head>
                    <body>
                        <h1>{titulo}</h1>
                        <video width="640" height="360" controls>
                            <source src="{url_firmada}" type="video/{formato_video}">
                            Tu navegador no soporta la etiqueta de video.
                        </video>
                    </body>
                    </html>
                """
        else:
            return "Archivo no encontrado", 404
    else:
        return "tipo archivo debe ser original o convertido", 400


@controllers.route('/tasks/<int:id>', methods=['DELETE'])
@jwt_required()
def eliminar_tareas(id):
    user_id = get_jwt_identity()
    estado = fileUtils.obtener_estado_tareas_por_id(id, user_id)
    if estado:
        if estado.estado == 'convertido':
            fileUtils.eliminar_archivo(id, user_id)
            fileUtils.eliminar_tarea(estado)
            return f"Tarea con el id {id} eliminada con exito", 200
        else:
            return f"La tarea con id {id} se encuentra en estado {estado.estado}, debe esperar a que termine de procesar", 200
    else:
        return f"Tarea no encontrada con id {id}", 404


@controllers.route('/tasks', methods=['GET'])
@jwt_required()
def obtener_tareas():
    user_id = get_jwt_identity()
    data = request.get_json()

    print(user_id)

    max_value = data.get("max")
    order_value = data.get("order")

    tareas = fileUtils.obtener_lista_tareas_usuario(user_id, max_value, order_value)
    return {"tareas": [estado_archivo_schema.dump(task) for task in tareas]}, 200
