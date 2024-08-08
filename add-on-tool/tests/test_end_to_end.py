import pytest
import re
from seeq import spy, sdk
from urllib.parse import urlencode
import datetime
import pytz
from playwright.sync_api import expect, Page, APIRequestContext
from typing import Generator


@pytest.fixture
def add_on_query_params(
    api_request_context: APIRequestContext, page: Page, url: str, element_identifier
) -> Generator[dict, None, None]:
    """
    Creates basic workbook for e2e test using workbook url builder
    """
    browser_context = page.context.browser.new_context(
        storage_state=api_request_context.storage_state()
    )
    workbench_page = browser_context.new_page()
    workbench_query_params = {
        "trendItems": "Example>>Cooling Tower 1>>Area B>>Temperature",
        "workbookName": f"{element_identifier} {datetime.datetime.now(pytz.utc).isoformat()}",
    }
    workbook_builder_url = (
        f"{url}/workbook/builder/?{urlencode(workbench_query_params)}"
    )
    # capture the redirect to the built workbench
    workbench_page.goto(workbook_builder_url)
    workbench_page.wait_for_url("**/workbook/*/worksheet/*")
    expect(workbench_page.locator("id=header")).to_be_visible()

    workbook_id = spy.utils.get_workbook_id_from_url(workbench_page.url)
    worksheet_id = spy.utils.get_worksheet_id_from_url(workbench_page.url)
    yield {
        "workbookId": workbook_id,
        "worksheetId": worksheet_id,
    }

    # cleanup - delete workbook
    sdk.ItemsApi(spy.client).archive_item(id=workbook_id)


# To lookup a datalab project ID, parametrize the test
# and specify the path for the element we want to grab the project ID for.
# Specify the path from the root of the project
@pytest.mark.end_to_end
@pytest.mark.parametrize("element_path", ["add-on-tool"])
def test_add_on(
    api_request_context: APIRequestContext,
    page: Page,
    url: str,
    project_id,
    element_config,
    add_on_query_params,
) -> None:
    """
    End to end test that uses a combination of SPy and Playwright:
    1. Creates a new workbook using the workbook builder
    2. Loads the add-on with the newly created workbook
    3. Fills out and executes the add-on
    4. Pulls the workbench with SPy to verity the expected worksheets were pushed
    """
    expected_worksheets = {
        "Temperature Control Chart",
        "Temperature Western Electric Run Rules",
        "Temperature Nelson Run Rules",
        "Temperature Histogram",
    }
    browser_context = page.context.browser.new_context(
        storage_state=api_request_context.storage_state()
    )
    # workbench_page = browser_context.new_page()
    # workbench_query_params = {
    #     "trendItems": "Example>>Cooling Tower 1>>Area B>>Temperature",
    #     "workbookName": f"{element_identifier} {datetime.datetime.now(pytz.utc).isoformat()}",
    # }
    # workbook_builder_url = (
    #     f"{url}/workbook/builder/?{urlencode(workbench_query_params)}"
    # )
    # # capture the redirect to the built workbench
    # workbench_page.goto(workbook_builder_url)
    # workbench_page.wait_for_url("**/workbook/*/worksheet/*")
    # expect(workbench_page.locator("id=header")).to_be_visible()

    # workbook_id = spy.utils.get_workbook_id_from_url(test_workbook_url)
    # worksheet_id = spy.utils.get_worksheet_id_from_url(test_workbook_url)

    # load the add-on with query parameters
    notebook_path = element_config["notebook_file_path"]
    # add_on_query_params = {
    #     "workbookId": workbook_id,
    #     "worksheetId": worksheet_id,
    # }
    add_on_url = f"""
    {url}/data-lab/{project_id}/addon/{notebook_path}?{urlencode(add_on_query_params)}
    """
    add_on_page = browser_context.new_page()
    add_on_page.goto(add_on_url)
    add_on_page.wait_for_selector(".v-toolbar__content")
    add_on_page.get_by_role("button", name="Input Signal").click()
    add_on_page.get_by_role("option", name="Temperature").click()
    add_on_page.get_by_text("Western Electric Run Rules").click()
    add_on_page.get_by_text("Nelson Run Rules").click()
    add_on_page.get_by_text("Histogram Normality Check").click()
    add_on_page.get_by_role("button", name="Execute").click()
    # once the link button is clickable, implies execution has completed.
    add_on_page.locator("div").filter(has_text=re.compile(r"^Execute$")).get_by_role(
        "link"
    ).click()

    workbook = spy.workbooks.pull(add_on_query_params["workbookId"])[0]
    worksheets = {ws.name for ws in workbook.worksheets}
    assert expected_worksheets.issubset(worksheets)
