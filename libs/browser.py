import logging

from playwright.async_api import async_playwright, PlaywrightContextManager, Playwright, Browser, Page, BrowserContext

log: logging.Logger = logging.getLogger("browser")


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
        log.debug('headless Chromium 브라우저 시작')

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
        log.debug('새 컨텍스트 열기')
        self.context: BrowserContext = await self.browser.new_context()

        return self

    async def new_page(self):
        log.debug('새 페이지 열기')
        self.page: Page = await self.context.new_page()
        return self.page

    async def pdf(self):
        # https://playwright.dev/python/docs/api/class-page#page-pdf
        log.debug('PDF로 변환 및 저장')
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

        log.debug('브라우저 종료')

        # https://playwright.dev/python/docs/api/class-browser#browser-close
        await self.browser.close()

        # https://playwright.dev/python/docs/api/class-playwright#playwright-stop
        await self.playwright.stop()
