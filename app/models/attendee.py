from models import db


class Attendee(db.Document):
    token = db.StringField()
    name = db.StringField()
    phone = db.StringField()
    status = db.BooleanField()

    meta = {
        'indexes': [
            '$token'
        ]
    }
