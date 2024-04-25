import pytest
import sys
import os
import json
from seeq import spy
from playwright.sync_api import sync_playwright, expect, Page, APIRequestContext


@pytest.mark.system
def test_add_on_loads(
    api_request_context: APIRequestContext, page: Page, url: str, spy_session
) -> None:
    browser_context = page.context.browser.new_context(
        storage_state=api_request_context.storage_state()
    )
    print(browser_context.storage_state())
    homepage = browser_context.new_page()
    homepage.goto(f"{url}/workbooks")
    expect(homepage).to_have_title("Seeq")
    expect(homepage.locator("id=myFolder")).to_be_visible(timeout=1000)
