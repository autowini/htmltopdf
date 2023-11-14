import logging

import pytest
from playwright.async_api import async_playwright, Playwright, PlaywrightContextManager, Browser, BrowserContext

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.asyncio
async def test_core_file():
    """
    cat <<EOT> test_core.py
    {this_file}
    EOT

    and `pytest`
    """

    # NOTE: `playwright install chromium` # or firefox, webkit
    # Download to $HOME/.cache/ms-playwright/
    playwright_context_manager: PlaywrightContextManager = async_playwright()

    # https://playwright.dev/python/docs/api/class-playwright
    playwright: Playwright = await playwright_context_manager.start()

    # https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
    browser: Browser = await playwright.chromium.launch(
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
    logging.debug('새 컨텍스트 열기')
    context: BrowserContext = await browser.new_context()
    page = await context.new_page()

    # https://playwright.dev/python/docs/api/class-page#page-goto
    logging.debug('Content 생성')
    await page.set_content(
        html='<div><span>Test</span> Text</div>',
        timeout=10_000,
        # load로 해야 img.src가 로드됨.
        wait_until='load'  # domcontentloaded, load, networkidle
    )

    logging.info('CSS 추가')
    await page.add_style_tag(
        content='span{color:red;}'
    )

    # https://playwright.dev/python/docs/api/class-page#page-pdf
    logging.debug('PDF로 변환 및 저장')
    _pdf = await page.pdf(
        format='A4',
        landscape=False,
        print_background=True,
        display_header_footer=False,
        margin={
            'top': '10mm',
            'bottom': '10mm',
            'left': '10mm',
            'right': '10mm',
        }
    )

    print(_pdf)

    await context.close()  # don't forget to close the context, or it will create a core.{number} file.
    await browser.close()
    await playwright.stop()
