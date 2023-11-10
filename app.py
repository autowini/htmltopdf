import logging
import sys

from flask import Flask
from flask_cors import CORS

from api.errorhandlers import setup_errorhandlers
from api.pdf_from_content import get_pdf_from_content
from api.pdf_from_url import get_pdf_from_url

app = Flask(__name__)

setup_errorhandlers(app)

if __name__ == '__main__':
    logging_format = '%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(name)s:%(module)s] - %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,
        filename='logs/htmltopdf.log',
        filemode='a+',  # 'a': append, 'w': overwrite
        format=logging_format,
    )

    # root 로거 설정
    root_logger: logging.Logger = logging.getLogger()
    # Standard output을 위한 StreamHandler 설정
    # Docker에서는 stdout으로 로그를 확인할 수 있음.
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(logging_format))
    root_logger.addHandler(stream_handler)

    # Werkzeug (Flask) 로그 설정
    flask_logger: logging.Logger = app.logger
    flask_logger.setLevel(logging.DEBUG)
    logging.getLogger('websockets').setLevel(logging.INFO)

    CORS(app, resources={r"*": {"origins": "*"}})

    app.add_url_rule(rule='/pdf/url', view_func=get_pdf_from_url, methods=['GET'])
    app.add_url_rule(rule='/pdf/content', view_func=get_pdf_from_content, methods=['POST'])

    app.run(
        host="0.0.0.0",  # 명시하지 않으면 `localhost`만 인식함.
        port=5000,
        use_reloader=False,
        debug=True,  # 개발 시 `True`로 설정
    )
