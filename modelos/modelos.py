from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import Enum
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

EstadoEnum = Enum('Ingresado','procesando', 'convertido', 'fallido', name='estado_enum')


class EstadoArchivos(db.Model):
    __tablename__ = 'estado_archivos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_archivo = db.Column(db.String(128))
    nuevo_archivo = db.Column(db.String(128))
    estado = db.Column(EstadoEnum, nullable=False)
    extension_original = db.Column(db.String(128))
    extension_nueva = db.Column(db.String(128))
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_procesamiento = db.Column(db.DateTime)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


class EstadoArchivosSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EstadoArchivos
        include_relationships = True
        load_instance = True
        include_fk = True

    id = fields.String()


class UsersSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        include_relationships = True
        load_instance = True
        include_fk = True

    id = fields.String()
