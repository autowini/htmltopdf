import json

from flask import Response
from werkzeug.routing import ValidationError


def setup_errorhandlers(app):
    @app.errorhandler(400)
    @app.errorhandler(ValidationError)
    def handle_bad_request(exception):
        app.logger.error(f"{type(exception)}-{exception}")
        res: dict[str, str] = {
            "message": exception.args[0]
        }
        return Response(
            response=json.dumps(res),
            mimetype='application/json',
            status=400,
        )

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def handle_internal_server_error(exception):
        app.logger.error(f"{type(exception)}-{exception}")
        res: dict[str, str] = {
            "message": "Something went wrong. Please try again later."
        }
        return Response(
            response=json.dumps(res),
            mimetype='application/json',
            status=500,
        )
