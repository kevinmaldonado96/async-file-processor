from flask import Blueprint, request, jsonify, url_for, send_from_directory

bluePrintHealthcheckController = Blueprint('bluePrintHealthcheckController', __name__)

@bluePrintHealthcheckController.route("/ping", methods=['GET'])
def healthcheck():
    return "pong", 200