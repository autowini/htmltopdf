import asyncio
import json
import logging
import sys

from flask import Flask, Response, request
from flask_cors import CORS

from libs.pdf import url_to_pdf, content_to_pdf
from libs.perf import print_elapsed_time

app = Flask(__name__)


@app.errorhandler(Exception)
def handle_bad_request(exception):
    app.logger.error(f"{type(exception)}-{exception}")
    res: dict[str, str] = {
        "message": exception.args[0]
    }
    return Response(
        response=json.dumps(    res),
        mimetype='application/json',
        status=500,
    )


@app.get(rule='/pdf/url')
@print_elapsed_time
def get_pdf_from_url():
    # req_param: dict = request.json
    req_param: dict = request.args.to_dict()  # ImmutableMultiDict -> dict

    loop = asyncio.new_event_loop()
    pdf_binary_data = loop.run_until_complete(
        url_to_pdf(
            url=req_param.get('url'),
            orientation=req_param.get('orientation', 'portrait')
        )
    )

    filename = req_param.get('filename', 'output')
    return Response(
        response=pdf_binary_data,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment;filename={filename}.pdf'
        }
    )


@app.post(rule='/pdf/content')
@print_elapsed_time
def get_pdf_from_content():
    _form = request.form

    _html = _form.get('html')
    # app.logger.debug(_html)
    if _html is None:
        raise ValueError('html is required.')

    loop = asyncio.new_event_loop()
    pdf_binary_data = loop.run_until_complete(
        content_to_pdf(
            html=_html,
            css=_form.get('css'),
            orientation=_form.get('orientation', None)
        )
    )

    filename = _form.get('filename', 'output')
    return Response(
        response=pdf_binary_data,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment;filename={filename}.pdf'
        }
    )


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

    app.run(
        host="0.0.0.0",  # 명시하지 않으면 `localhost`만 인식함.
        port=5000,
        use_reloader=True,
        debug=True,  # 개발 시 `True`로 설정
    )
