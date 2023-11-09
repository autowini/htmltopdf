import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, Response, request
from flask_cors import CORS
from playwright.async_api import async_playwright, PlaywrightContextManager, Playwright

app = Flask(__name__)


# logging decorator
def print_elapsed_time(func):
    @wraps(func)
    def wrapper(**kwargs):
        start = datetime.now()
        app.logger.info(f"start: {start}")

        # 함수 실행
        result = func(**kwargs)

        # 현재 Epoch time 얻기
        end = datetime.now()
        app.logger.info(f"end: {end}")

        elapsed_time: timedelta = (end - start)
        formatted_elapsed_time = "{:.3f}".format(elapsed_time.total_seconds())
        app.logger.info(
            f"Elapsed time for function: {formatted_elapsed_time} s")

        return result

    return wrapper


async def url_to_pdf(
        url: str,
        orientation: str = 'portrait',
):
    # NOTE: `playwright install chromium` # or firefox, webkit
    # Download to $HOME/.cache/ms-playwright/
    app.logger.debug('headless Chromium 브라우저 시작')

    # https://playwright.dev/python/docs/api/class-playwright
    playwright_context_manager: PlaywrightContextManager = async_playwright()
    playwright: Playwright = await playwright_context_manager.start()

    # https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
    browser = await playwright.chromium.launch(
        headless=True,
        timeout=10_000,  # (ms)
        args=[
            # https://peter.sh/experiments/chromium-command-line-switches/
            "--no-sandbox",
            "--single-process",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-zygote",
        ],
        # avoid "signal only works in main thread of the main interpreter"
        handle_sigint=False,
        handle_sigterm=False,
        handle_sighup=False,
    )

    app.logger.debug('새 컨텍스트 열기')
    # https://playwright.dev/python/docs/api/class-browser#browser-new-context
    context = await browser.new_context()

    app.logger.debug('새 페이지 열기')
    page = await context.new_page()

    app.logger.debug('URL로 이동')
    # FIXME: 접근할 수 없는 페이지, 서버가 응답하지 않는 페이지 등을 요청하는 경우
    # 해당 이벤트 루프가 상위 레이어에서 타임아웃 발생할 때까지 대기함.
    # https://playwright.dev/python/docs/api/class-page#page-goto
    await page.goto(url=url, timeout=10_000, wait_until='domcontentloaded')

    app.logger.debug('PDF로 변환 및 저장')
    _landscape = orientation == 'landscape'
    app.logger.debug(f'landscape: {_landscape}')
    # https://playwright.dev/python/docs/api/class-page#page-pdf
    _pdf = await page.pdf(
        format='A4',
        landscape=_landscape,
        print_background=True,
        display_header_footer=False,
        margin={
            'top': '10mm',
            'bottom': '10mm',
            'left': '10mm',
            'right': '10mm',
        }
    )

    # https://playwright.dev/python/docs/api/class-browser#browser-close
    app.logger.debug('브라우저 종료')
    await browser.close()
    # https://playwright.dev/python/docs/api/class-playwright#playwright-stop
    await playwright.stop()

    return _pdf


@app.route(rule='/pdf/url', methods=['GET'])
@print_elapsed_time
def get_pdf_from_url():
    # req_param: dict = request.json
    req_param: dict = request.args.to_dict()  # ImmutableMultiDict -> dict

    try:
        _url = req_param.get('url')
        app.logger.info(_url)

        _orientation = req_param.get('orientation', 'portrait')

        loop = asyncio.new_event_loop()
        pdf_binary_data = loop.run_until_complete(
            url_to_pdf(
                url=_url,
                orientation=_orientation
            )
        )

    except Exception as exception:
        app.logger.error(f"{type(exception)}-{exception}")
        res: dict[str, str] = {
            "message": "Something went wrong. Please try again later."
        }
        return Response(
            response=json.dumps(res),
            mimetype='application/json',
            status=500,
        )
    filename = req_param.get('filename', 'output')

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
