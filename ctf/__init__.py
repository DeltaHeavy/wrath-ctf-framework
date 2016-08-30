import json
import os
import flask
import redis
from werkzeug import exceptions
from . import api, frontend, ext
from .models import db


def create_app():
    app = flask.Flask(__name__)
    config_file = "./ctf.json"

    if 'CTF_CONFIG' in os.environ:
        config_file = os.enviorn['CTF_CONFIG']
    
    with open(config_file, 'r') as config:
        app.config['CTF'] = json.load(config)

    if "secret_key" not in app.config['CTF']:
        app.config['CTF']['secret_key'] = "not secure brah"


    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL',
                                                           'sqlite:///test.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.redis = redis.StrictRedis()

    # Setup extensions
    ext.db.init_app(app)
    ext.csrf.init_app(app)

    @app.before_first_request
    def create_db():
        db.create_all()

    @app.context_processor
    def inject_authed():
        """This should NOT be used to secure access control.

        The aim of the 'authed' global is simply better link rendering in
        templates.
        """
        return {'authed': 'key' in flask.session}

    def handle_error(exc):
        if not isinstance(exc, exceptions.HTTPException):
            exc = exceptions.InternalServerError()
        return flask.render_template('error.html', code=exc.code), exc.code

    for code in exceptions.default_exceptions.keys():
        app.register_error_handler(code, handle_error)

    app.register_blueprint(frontend.bp)
    app.register_blueprint(api.bp, url_prefix='/api')

    return app
