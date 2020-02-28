import requests

from error import Error
from flask import Flask, request, jsonify
from mongoengine.queryset import DoesNotExist, ValidationError
from models import db, Attendee

import config


app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init_app(app)


def get_attendee(token=None, id=None):

    if token is None and id is None:
        raise Error("Identification required")

    try:
        if token is not None:
            attendee = Attendee.objects(token=token).get()
        else:
            attendee = Attendee.objects().get(id=id)
    except DoesNotExist:
        attendee = None
    except ValidationError:
        raise Error("Invalid id")

    return attendee


@app.errorhandler(Error)
def handle_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/status')
def status():
    token = request.args.get('token')
    id = request.args.get('id')

    attendee = get_attendee(token, id)

    if token is not None and attendee is None:
        payload = {'token': token}
        r = requests.get(config.AUTH_ENDPOINT, params=payload)

        if r.status_code != 200:
            raise Error("Invalid token")

    if attendee is None:
        return jsonify({'fill': False})

    if attendee.status is True:
        return jsonify({'fill': True, 'status': True})

    return jsonify({'fill': True, 'status': False})


@app.route('/fill', methods=['POST'])
def fill():
    token = request.form.get('token')
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    status = request.form.get('status')

    if token is not None:
        attendee = get_attendee(token=token)
        if attendee is not None:
            raise Error("Aleady fill the form")

    attendee = Attendee()
    attendee.name = name
    attendee.phone = phone
    attendee.address = address
    attendee.status = (status == "true")
    attendee.save()

    return jsonify({'fill': True, 'id': str(attendee.id)})
