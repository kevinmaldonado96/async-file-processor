from flask import Flask
from modelos import db
from datetime import timedelta



class Config:

    @staticmethod
    def init():
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@34.132.16.5:5432/conversor'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = 'frase-secreta'
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=10)
        app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
        app.config['PROPAGATE_EXCEPTIONS'] = True

        app_context = app.app_context()
        app_context.push()

        db.init_app(app)
        db.create_all()
        return app
