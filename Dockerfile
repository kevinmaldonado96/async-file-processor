######################################################
#                       TEMPORAL
######################################################
# Utiliza una imagen oficial de Python como imagen base
FROM python:3.9

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia las credenciales del servicio de usuario de almacenamiento
COPY credentials.json .

# Modifica los permisos
RUN chmod 775 /app/credentials.json

# Establece la variable de entorno para las credenciales de Google Cloud
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/credentials.json"

# Copia el resto del código de la aplicación al contenedor
COPY . .

# Copia el archivo de requisitos en el contenedor
COPY app.py .

# Copia el binario de ffmpeg directamente (ajusta la URL según la versión y arquitectura necesaria)
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar -xvf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    rm -rf ffmpeg-release-amd64-static.tar.xz ffmpeg-*-amd64-static/

# Instala las dependencias de Python
RUN pip install -r requirements.txt

# Expone el puerto en el que se ejecutará tu aplicación Flask
EXPOSE 5000

# Define el comando para iniciar tu aplicación Flask
CMD ["flask", "run", "--host=0.0.0.0"]
