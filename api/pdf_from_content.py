import asyncio
import threading

from flask import current_app as app
from flask import request, Response
from werkzeug.routing import ValidationError

from libs.pdf import content_to_pdf
from libs.perf import print_elapsed_time


@print_elapsed_time
def get_pdf_from_content():
    _form = request.form

    _html = _form.get('html')
    # app.logger.debug(_html)
    if _html is None:
        raise ValidationError('<html> is required.')

    pdf_binary_data = asyncio.run(
        content_to_pdf(
            html=_html,
            css=_form.get('css'),
            orientation=_form.get('orientation', None)
        )
    )
    app.logger.debug(f"threading.active_count(): {threading.active_count()}")

    filename = _form.get('filename', 'output')
    return Response(
        response=pdf_binary_data,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment;filename={filename}.pdf'
        }
    )
