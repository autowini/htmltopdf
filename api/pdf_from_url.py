import asyncio

from flask import request, Response
from werkzeug.routing import ValidationError

from libs.pdf import url_to_pdf
from libs.perf import print_elapsed_time


@print_elapsed_time
def get_pdf_from_url():
    # req_param: dict = request.json
    req_param: dict = request.args.to_dict()  # ImmutableMultiDict -> dict

    _url = req_param.get('url')
    if _url is None:
        raise ValidationError("<url> is required.")

    pdf_binary_data = asyncio.run(
        url_to_pdf(
            url=_url,
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
