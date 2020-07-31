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
    email = request.form.get('email')
    status = request.form.get('status')
    is_ccip_user = False

    if status == "false":
        raise Error("Rest at home")

    if token is not None:
        attendee = get_attendee(token=token)
        if attendee is not None:
            raise Error("Already fill the form")

        payload = {'token': token}
        r = requests.get(config.AUTH_ENDPOINT, params=payload)

        if r.status_code != 200:
            raise Error("Invalid token")

        is_ccip_user = True

    attendee = Attendee()
    if is_ccip_user:
        attendee.token = token
    attendee.name = name
    attendee.phone = phone
    attendee.email = email
    attendee.status = (status == "true")
    attendee.save()

    if config.CREATE_ATTENDEE_ENDPOINT is not None and not is_ccip_user:
        payload = {
            'token': str(attendee.id),
            'name': name
        }

        requests.post(config.CREATE_ATTENDEE_ENDPOINT, data=payload)

        attendee.token = str(attendee.id)
        attendee.save()

    return jsonify({'fill': True, 'id': str(attendee.id)})
