from api.models import db


def add_flush_(db_model_object):
    if isinstance(db_model_object, list):
        db.session.add_all(db_model_object)
    else:
        db.session.add(db_model_object)
    db.session.flush()


def commit_():
    db.session.commit()


def add_commit_(db_model_object):
    add_flush_(db_model_object)
    commit_()


def delete_commit_(db_model_object):
    db.session.delete(db_model_object)
    commit_()
