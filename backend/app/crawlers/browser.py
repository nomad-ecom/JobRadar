from app.crawlers.http import USER_AGENT, FetchError
from app.config import get_settings


def playwright_fetch(url: str) -> tuple[int, str, str]:
    """Open a public page in Chromium and return the HTML. Stops on HTTP errors. No stealth."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FetchError("Chưa cài playwright. Cài nhóm phụ thuộc browser rồi chạy playwright install chromium.") from exc

    settings = get_settings()
    launch_args: dict = {"headless": True}
    if settings.chrome_path:
        launch_args["executable_path"] = settings.chrome_path
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**launch_args)
            page = browser.new_page(user_agent=USER_AGENT)
            response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            status = response.status if response is not None else 0
            if status < 400:
                page.wait_for_timeout(1200)
            body = page.content()
            browser.close()
    except FetchError:
        raise
    except Exception as exc:
        raise FetchError(str(exc)) from exc
    return status, body, "text/html"
