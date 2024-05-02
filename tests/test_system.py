import pytest
import sys
import os
import json
from seeq import spy
from playwright.sync_api import sync_playwright, expect, Page, APIRequestContext


# To lookup a datalab project ID, parametrize the test
# and specify the path for the element we want to grab the project ID for.
# Specify the path from the root of the project
@pytest.mark.system
@pytest.mark.parametrize("element_path", ["add-on-tool"])
def test_add_on_loads(
    api_request_context: APIRequestContext,
    page: Page,
    url: str,
    spy_session,
    project_id,
    element_config,
) -> None:
    browser_context = page.context.browser.new_context(
        storage_state=api_request_context.storage_state()
    )
    workbench_page = browser_context.new_page()
    workbook_builder_url = f"""
    {url}/workbook/builder?trendItems=Example>>Cooling Tower 1>>Area B>>Temperature
    """
    # capture the redirect to the built workbench
    workbench_page.goto(workbook_builder_url)
    workbench_page.wait_for_url("**/workbook/*/worksheet/*")
    expect(workbench_page.locator("id=header")).to_be_visible()

    workbench_url = workbench_page.url
    workbook_id = spy._url.get_workbook_id_from_url(workbench_url)
    worksheet_id = spy._url.get_worksheet_id_from_url(workbench_url)

    # load the add-on with query parameters
    notebook_path = element_config["notebook_file_path"]
    add_on_url = f"""
    {url}/data-lab/{project_id}/addon/{notebook_path}?workbookId={workbook_id}&worksheetId={worksheet_id}
    """
    add_on_page = browser_context.new_page()
    add_on_page.goto(add_on_url)
    add_on_page.wait_for_selector(".v-toolbar__content", timeout=10000)
    add_on_page.screenshot(path="add-on.png")
