"""Synthetic Chromium regressions; all API traffic is intercepted and local."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def fixture(browser, assets, blocked_storage=False):
    page = browser.new_page(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    if blocked_storage:
        page.add_init_script(
            "Object.defineProperty(window, 'localStorage', {get(){throw new DOMException('Synthetic denied storage', 'SecurityError')}})"
        )

    def route(request):
        from urllib.parse import urlparse

        url = urlparse(request.request.url)
        if url.hostname != "synthetic.test":
            request.abort()
        elif url.path in assets:
            kind = (
                "text/css"
                if url.path.endswith(".css")
                else "text/javascript"
                if url.path.endswith(".js")
                else "text/html"
            )
            body = assets[url.path] + (
                ";window.__syntheticAppReady=true;" if url.path.endswith(".js") else ""
            )
            request.fulfill(body=body, content_type=kind)
        elif url.path.startswith("/v1/"):
            request.fulfill(json={"execution_mode": "mock", "runtime_credentials_allowed": False})
        else:
            request.abort()

    page.route("**/*", route)
    page.goto("https://synthetic.test/")
    page.wait_for_function("window.__syntheticAppReady === true")
    return page, errors


def run(browser):
    base = ROOT / "src/reflection_ai/frontend"
    assets = {
        "/": (base / "chat.html").read_text(),
        "/chat-assets/chat.css": (base / "chat.css").read_text(),
        "/chat-assets/chat.js": (base / "chat.js").read_text(),
    }
    page, errors = fixture(browser, assets)
    page.evaluate(
        "()=>{showPanel(chat); for(let i=0;i<45;i++) addMessage({id:'synthetic-'+i,role:i%2?'assistant':'user',content:'SYNTHETIC scroll fixture '+i+'\\nSecond line\\nThird line'},false); messages.scrollTop=120}"
    )
    before = page.locator("#messages").evaluate("el=>el.scrollTop")
    assert (
        page.locator("#messages").evaluate("el=>el.scrollHeight-el.clientHeight-el.scrollTop")
        > 1000
    )
    page.evaluate(
        "addMessage({id:'synthetic-new',role:'assistant',content:'SYNTHETIC delayed append'},false)"
    )
    assert page.locator("#messages").evaluate("el=>el.scrollTop") == before
    page.locator("#jump-latest").click()
    assert (
        page.locator("#messages").evaluate("el=>el.scrollHeight-el.clientHeight-el.scrollTop") <= 1
    )
    page.evaluate(
        "addMessage({id:'synthetic-follow',role:'assistant',content:'SYNTHETIC following append'},false)"
    )
    assert (
        page.locator("#messages").evaluate("el=>el.scrollHeight-el.clientHeight-el.scrollTop") <= 1
    )
    assert not errors, errors
    page.close()
    page, errors = fixture(browser, assets, True)
    assert "Server data is still retained" in page.locator("#session-storage-status").text_content()
    page.evaluate(
        "async()=>{state.sessionId='synthetic-session'; state.userId='synthetic-user'; saveSession(); await refreshInspector()}"
    )
    assert "out of date" in page.locator("#inspector-status").text_content()
    page.locator("#inspector-toggle").click()
    assert page.locator("#learning-toggle").is_disabled()
    page.locator("#inspector-retry").wait_for(state="visible")
    page.locator("#enter-to-send").uncheck()
    page.locator("#inspector-close").click()
    page.evaluate("showPanel(chat)")
    page.locator("#message-input").fill("SYNTHETIC LINE")
    page.locator("#message-input").press("Enter")
    assert page.locator("#message-input").input_value() == "SYNTHETIC LINE\n"
    assert not errors, errors
    page.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        options = {"headless": True}
        if os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"):
            options["executable_path"] = os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"]
        browser = playwright.chromium.launch(**options)
        try:
            run(browser)
            print("Synthetic browser regressions passed")
        finally:
            browser.close()
