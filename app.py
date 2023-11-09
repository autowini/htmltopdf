import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, Response, request
from flask_cors import CORS
from playwright.async_api import async_playwright, PlaywrightContextManager, Playwright, Browser, Page, BrowserContext

app = Flask(__name__)


def print_elapsed_time(func):
    """
    함수 실행 시간을 로그로 출력하는 데코레이터
    :param func:  함수
    :return:      함수 실행 시간을 로그로 출력
    """

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


class BrowserInstance:
    """
    Local에서 실행되는 Playwright 브라우저
    """

    def __init__(
            self,
            orientation: str = 'portrait',
            browser_type: str = 'chromium',
    ):
        self.browser_type = browser_type
        self.playwright_context_manager: PlaywrightContextManager = async_playwright()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._landscape: bool = orientation == 'landscape'

    async def start(self):
        # NOTE: `playwright install chromium` # or firefox, webkit
        # Download to $HOME/.cache/ms-playwright/
        app.logger.debug('headless Chromium 브라우저 시작')

        # https://playwright.dev/python/docs/api/class-playwright
        self.playwright: Playwright = await self.playwright_context_manager.start()

        # https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
        self.browser: Browser = await self.playwright.chromium.launch(
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

        # https://playwright.dev/python/docs/api/class-browser#browser-new-context
        app.logger.debug('새 컨텍스트 열기')
        self.context: BrowserContext = await self.browser.new_context()

        return self

    async def new_page(self):
        app.logger.debug('새 페이지 열기')
        self.page: Page = await self.context.new_page()
        return self.page

    async def pdf(self):
        # https://playwright.dev/python/docs/api/class-page#page-pdf
        app.logger.debug('PDF로 변환 및 저장')
        return await self.page.pdf(
            format='A4',
            landscape=self._landscape,
            print_background=True,
            display_header_footer=False,
            margin={
                'top': '10mm',
                'bottom': '10mm',
                'left': '10mm',
                'right': '10mm',
            }
        )

    async def stop(self):
        if self.browser is None:
            return

        app.logger.debug('브라우저 종료')

        # https://playwright.dev/python/docs/api/class-browser#browser-close
        await self.browser.close()

        # https://playwright.dev/python/docs/api/class-playwright#playwright-stop
        await self.playwright.stop()


async def url_to_pdf(
        url: str,
        orientation: str = 'portrait',
):
    app.logger.info(url)

    browser_instance = BrowserInstance(orientation=orientation)
    browser = await browser_instance.start()
    page = await browser.new_page()

    # https://playwright.dev/python/docs/api/class-page#page-goto
    app.logger.debug('URL로 이동')
    await page.goto(
        url=url,
        timeout=10_000,
        wait_until='load'  # domcontentloaded, load, networkidle
    )

    _pdf = await browser.pdf()

    await browser.stop()

    return _pdf


@app.route(rule='/pdf/url', methods=['GET'])
@print_elapsed_time
def get_pdf_from_url():
    # req_param: dict = request.json
    req_param: dict = request.args.to_dict()  # ImmutableMultiDict -> dict

    try:
        loop = asyncio.new_event_loop()
        pdf_binary_data = loop.run_until_complete(
            url_to_pdf(
                url=req_param.get('url'),
                orientation=req_param.get('orientation', 'portrait')
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


async def content_to_pdf(
        html: str,
        css: str,
        orientation: str = 'portrait',
):
    browser_instance = BrowserInstance(orientation=orientation)
    browser = await browser_instance.start()
    page = await browser.new_page()

    # https://playwright.dev/python/docs/api/class-page#page-goto
    app.logger.debug('Content 생성')
    await page.set_content(
        html=html,
        timeout=10_000,
        # load로 해야 img.src가 로드됨.
        wait_until='load'  # domcontentloaded, load, networkidle
    )
    if css is not None:
        app.logger.info('CSS 추가')
        # # for testing: addStyleTag가 적용되는지 확인
        # color = '#ff000091'
        # css += (f'\nbody {{ background-color: {color}; }}'
        #         f'\n#printzone {{ background-color: {color}; }}'
        #         f'\n.subpage {{ background-color: {color}; }}')
        # app.logger.debug(css)
        await page.add_style_tag(
            content=css
        )

    _pdf = await browser.pdf()

    await browser.stop()

    return _pdf


@app.route(rule='/pdf/content', methods=['POST'])
@print_elapsed_time
def get_pdf_from_content():
    _form = request.form
    try:
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
