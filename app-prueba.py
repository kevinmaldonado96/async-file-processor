from flask import Flask
from flask_cors import CORS
from configuracion import Config
from flask_jwt_extended import JWTManager

app = Flask(__name__)

app = Config.init()

cors = CORS(app)



from controllers import controllers

app.register_blueprint(controllers, url_prefix='/api')

jwt = JWTManager(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
