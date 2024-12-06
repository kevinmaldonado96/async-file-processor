
import subprocess
import argparse
from datetime import datetime, timedelta

from modelos import EstadoArchivos, db, Users
import os
import logging
import re
from google.cloud import storage
from google.cloud import pubsub_v1
import json
from google.auth import jwt



def eliminar_archivo(ruta_absoluta):
    print(f'Eliminando archivo {ruta_absoluta}')
    # Elimina el archivo temporal del sistema de archivos local
    os.remove(ruta_absoluta)


class FileUtils:
    NOMBRE_BUCKET = "video_format_converter_v2"
    URL_BUCKET = "https://storage.googleapis.com/video_format_converter_v2/"
    PROJECT_ID = "conversor-grupo-10-v2"
    TOPIC_ID = "video_format_converter_topic_v2"
    SUBSCRIPTION = "video_format_converter_topic_v2-sub"

    def procesar_elemento_cola(self, id):
        logging.info(f"ejecutando cola con id {id}")

        try: 
            estado_archivo = EstadoArchivos.query.get(id)
            self.editar_estado_documento(estado_archivo.id, 'procesando', '', datetime.now())
            
            nombre_archivo_convertido = f"{estado_archivo.id}_converted.{estado_archivo.extension_nueva}"

            if estado_archivo.extension_nueva == 'mp4':
                self.convertir_archivo(estado_archivo.nombre_archivo, nombre_archivo_convertido)
            if estado_archivo.extension_nueva == 'webm':
                logging.info('entre webm')
                self.convertir_archivo(estado_archivo.nombre_archivo, nombre_archivo_convertido)
            if estado_archivo.extension_nueva == 'avi':
                self.convertir_archivo(estado_archivo.nombre_archivo, nombre_archivo_convertido)

            self.editar_estado_documento(estado_archivo.id, 'convertido', nombre_archivo_convertido,datetime.now())

            print(f"ejecutando cola con id {id} exitoso")

        except Exception as e:
            print(f"error a la hora de procesar la cola con id {id} {e}")
            self.editar_estado_documento(estado_archivo.id, 'fallido', '', datetime.now())


    def validar_request(self, extension_original, extension_convertir):
        if self.validar_extension_servicio_invalida(extension_original):
            return "el archivo adjunto no es valido, recuerda que debe ser mp4, webm o avi"
        if self.validar_extension_servicio_invalida(extension_convertir):
            return "la extensión ingresada para convertir no es valida, recuerda que debe ser mp4, webm o avi"
        if self.validar_extensiones_iguales(extension_original, extension_convertir):
            return "la extension del archivo ingresado y la extensión a compartir no deben ser las mismas"
        return ''

    def validar_extension_servicio_invalida(self, extension):
        if extension == 'mp4' or extension == 'webm' or extension == 'avi' :
            return False
        else:
            return True
        
    def validar_extensiones_iguales(self, extension_original, extension_convertir):
        if extension_original == extension_convertir:
            return True
        else:
            return False
        
    def guardar_archivo_original(self, archivo, id):
        ruta_relativa = os.path.join('.', 'files/original/')
        ruta_absoluta = os.path.abspath(ruta_relativa)

        logging.info(ruta_absoluta)
        if not os.path.exists(ruta_absoluta):
           os.makedirs(ruta_absoluta)
        nombre_archivo_guardado = f"{id}_{archivo.filename}"
        archivo_guardado = os.path.join(ruta_absoluta, f"{nombre_archivo_guardado}")
        print(f'Archivo_original ================> {archivo_guardado}')
        archivo.save(archivo_guardado)
        self.subir_video_bucket(nombre_archivo_guardado, ruta_absoluta, 'original')
        #print(archivo_guardado)
        #archivo.save(archivo_guardado)

    def convertir_archivo(self, nombre_archivo, nombre_archivo_convertido):
        ruta_relativa_original = os.path.join('.', 'files/original')
        ruta_absoluta_original = os.path.abspath(ruta_relativa_original)
        
        logging.info(ruta_absoluta_original)
        
        ruta_relativa_convertidos = os.path.join('.','files/convertido')
        ruta_absoluta_convertidos = os.path.abspath(ruta_relativa_convertidos)
        
        logging.info(ruta_absoluta_convertidos)
        
        if not os.path.exists(ruta_absoluta_convertidos):
           os.makedirs(ruta_absoluta_convertidos)

        ruta_absoluta_convertido = os.path.join(ruta_absoluta_convertidos, nombre_archivo_convertido)

        ruta_archivo_convertir = os.path.join(ruta_absoluta_original, nombre_archivo)      
        self.escribir_archivo_convertido(ruta_archivo_convertir, ruta_absoluta_convertido)
        self.subir_video_bucket(nombre_archivo_convertido, ruta_absoluta_convertidos, 'convertido')
        eliminar_archivo(ruta_archivo_convertir)
        
    def escribir_archivo_convertido(self, ruta_archivo_convertir, ruta_absoluta_convertido):
        print(f"convirtiendo a {ruta_absoluta_convertido}")
        subprocess.call(['ffmpeg', '-i', ruta_archivo_convertir, ruta_absoluta_convertido])

    def crear_estado_documento(self, nombre_archivo, estado, extension_original, extension_convertir, usuario_id):
        estado_archivos = EstadoArchivos(
                nombre_archivo=nombre_archivo,
                extension_original=extension_original,
                extension_nueva=extension_convertir,
                estado=estado,
                nuevo_archivo='pending',
                usuario_id=usuario_id
        )   

        db.session.add(estado_archivos)
        
        estado_archivos.nombre_archivo
        db.session.commit()

        return estado_archivos
    def editar_nombre_documento(self, id, nombre_archivo):

        estado_archivo = EstadoArchivos.query.get(id)
        estado_archivo.nombre_archivo = nombre_archivo
        db.session.commit()

    def editar_estado_documento(self, id, estado, nombre_archivo_convertido, fecha):

        estado_archivo = EstadoArchivos.query.get(id)
        estado_archivo.estado = estado
        estado_archivo.nuevo_archivo = nombre_archivo_convertido
        estado_archivo.fecha_procesamiento = fecha
        db.session.commit()

    def obtener_estado_tareas_por_id(self, id, usuario_id):
        return EstadoArchivos.query.filter_by(id=id, usuario_id=usuario_id).first()

    def obtener_estado_tareas_por_estado_y_nuevo_archivo(self, id, estado, nombre_archivo):
        if estado == 'original':
            return EstadoArchivos.query.filter_by(usuario_id=id, nombre_archivo=nombre_archivo).first()
        else:
            return EstadoArchivos.query.filter_by(usuario_id=id, nuevo_archivo=nombre_archivo).first()

    
    def obtener_lista_tareas_usuario(self, usuario_id, max, order):
        query = db.session.query(EstadoArchivos)
        
        logging.info(usuario_id)

        query = query.filter_by(usuario_id=usuario_id)

        if order is not None:
            if order == 1:
                query = query.order_by(EstadoArchivos.id.asc())
            elif order == 0:
                query = query.order_by(EstadoArchivos.id.desc())
                
        if max is not None:
            query = query.limit(max)

        return query.all()
    
    def eliminar_tarea(self, estado):
        db.session.delete(estado)
        db.session.commit()                        

    def validar_email(self, email):
        # Expresión regular para validar correos electrónicos
        patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if re.match(patron, email):
            return True
        else:
            return False

    def validar_contrasena(self, contrasena):
        # Verificar que tenga al menos 8 caracteres
        if len(contrasena) < 8:
            return False

        # Verificar que contenga al menos una mayúscula
        if not re.search(r'[A-Z]', contrasena):
            return False

        # Verificar que contenga al menos una minúscula
        if not re.search(r'[a-z]', contrasena):
            return False

        # Verificar que contenga al menos un número
        if not re.search(r'\d', contrasena):
            return False

        # Contar cuántos caracteres no son ni mayúsculas, minúsculas, números ni símbolos
        caracteres_invalidos = len(re.findall(r'[^A-Za-z0-9!@#$%^&*]', contrasena))

        # Si no hay caracteres inválidos, la contraseña es válida
        if caracteres_invalidos == 0:
            return True
        else:
            return False

    def subir_video_bucket(self, nombre_archivo, ruta_absoluta_archivo, directorio):
        print(f"subiendo a bucket  {nombre_archivo}")

        storage_client = storage.Client()
        bucket = storage_client.bucket(self.NOMBRE_BUCKET)

        # Guarda el archivo en el sistema de archivos local
        ruta_local = os.path.join(ruta_absoluta_archivo, f"{nombre_archivo}")

        # Crea un objeto Blob en el bucket
        blob = bucket.blob(f"{directorio}/{nombre_archivo}")

        # Carga el archivo al bucket desde el sistema de archivos local
        with open(ruta_local, "rb") as file:
            blob.upload_from_file(file)

    def descargar_video(self, directorio, nombre_archivo):
        # Crea un cliente de almacenamiento
        storage_client = storage.Client()

        # Obtiene el bucket y el objeto (video)
        bucket = storage_client.bucket(self.NOMBRE_BUCKET)
        blob = bucket.blob(f"{directorio}/{nombre_archivo}")

        # Calcula el tiempo de expiración
        tiempo_expiracion = datetime.utcnow() + timedelta(seconds=3600)

        # Genera la URL de acceso firmada
        url_firmada = blob.generate_signed_url(expiration=tiempo_expiracion)

        return url_firmada

    def eliminar_archivo(self, id, user_id):
        # Crea un cliente de almacenamiento
        storage_client = storage.Client()

        estado_archivo = self.obtener_estado_tareas_por_id(id, user_id)

        if estado_archivo:
            # Obtiene el bucket y el objeto (video)
            bucket = storage_client.bucket(self.NOMBRE_BUCKET)
            blob = bucket.blob(f"original/{estado_archivo.nombre_archivo}")
            # Elimina el archivo del bucket
            blob.delete()

            blob = bucket.blob(f"convertido/{estado_archivo.nuevo_archivo}")
            # Elimina el archivo del bucket
            blob.delete()

    def pub(self, id_video) -> None:
        print("Publishes a message to a Pub/Sub topic.")
        logging.info(f"ejecutando pub/sub id_video {id_video}")
        # Initialize a Publisher client.
        client = pubsub_v1.PublisherClient()
        # Create a fully qualified identifier of form `projects/{project_id}/topics/{topic_id}`
        topic_path = client.topic_path(self.PROJECT_ID, self.TOPIC_ID)

        data = {"id_video": id_video}
        # When you publish a message, the client returns a future.
        api_future = client.publish(topic_path, json.dumps(data).encode())
        message_id = api_future.result()

