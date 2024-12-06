from controllers.healtcheckController import bluePrintHealthcheckController
from utils import FileUtils
from google.cloud import pubsub_v1
import json
import logging
from configuracion import Config
from flask_restful import Api

'''
celery_app = Celery('tasks', 
                    broker='redis://redis:6379/0')

@celery_app.task(name='conversor')
'''

NOMBRE_BUCKET = "video_format_converter_v2"
URL_BUCKET = "https://storage.googleapis.com/video_format_converter_v2/"
PROJECT_ID = "conversor-grupo-10-v2"
TOPIC_ID = "video_format_converter_topic_v2"
SUBSCRIPTION = "video_format_converter_topic_v2-sub"

def obtener_id_proceso(id):
    logging.info('creando contexto') 
    Config.init()
        
    logging.info('iniciando')
    fileUtils = FileUtils()
    fileUtils.procesar_elemento_cola(id)


subscriber = pubsub_v1.SubscriberClient()

# Forma el nombre completo de la suscripción
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION)

def callback(message):
    print(f"Received message: {message.data}")
    # Decodifica los datos del mensaje (bytes) a una cadena
    message_data_str = message.data.decode('utf-8')

    # Analiza la cadena JSON para obtener el valor del campo "data"
    try:
        message_json = json.loads(message_data_str)
        data_value = message_json.get('id_video')
        # Puedes agregar aquí la lógica para procesar el mensaje
        obtener_id_proceso(data_value)
        print(f"Received message with data: {data_value}")
        # Acknowledge the message para indicar que ha sido procesado
        message.ack()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")



# Crea la suscripción
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

print(f"Escuchando mensajes en la suscripción {subscription_path}")

app = Config.init()

app.register_blueprint(bluePrintHealthcheckController)

api = Api(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    # Espera a que la suscripción termine
    try:
        streaming_pull_future.result()
    except Exception as ex:
        print(f"Error en la suscripción: {ex}")
        streaming_pull_future.cancel()

