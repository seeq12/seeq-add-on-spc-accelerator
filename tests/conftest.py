import pytest
import os
import sys
import json
import time
import types
from seeq import spy
from playwright.sync_api import Playwright, APIRequestContext
from typing import Generator

BASE_HEADERS = {
    "Accept": "application/vnd.seeq.v1+json",
    "Content-Type": "application/vnd.seeq.v1+json",
}


# TODO Remove this hack -- just pass in from ao.py
here = os.path.dirname(__file__)
sys.path.append(os.path.join(here, ".."))
from ao import get_bootstrap_json

bootstrap_json = get_bootstrap_json()
_url = bootstrap_json.get("url")
username = bootstrap_json.get("username")
password = bootstrap_json.get("password")


@pytest.fixture(scope="session")
def url(pytestconfig):
    return _url


@pytest.fixture(scope="session")
def spy_session():
    session = spy.Session()
    session.options.allow_version_mismatch = True
    spy.login(
        username=username, password=password, url=_url, quiet=True, session=session
    )
    return session


@pytest.fixture(scope="session")
def api_request_context(
    url: str, playwright: Playwright, spy_session
) -> Generator[APIRequestContext, None, None]:
    headers = {
        "Accept": "application/vnd.seeq.v1+json",
        "Content-Type": "application/vnd.seeq.v1+json",
        "sq-auth": spy_session.client.auth_token,
    }
    request_context = playwright.request.new_context(
        base_url=url, extra_http_headers=headers
    )
    yield request_context
    request_context.dispose()


# TODO: Why can't we use an access token for this?


@pytest.fixture(scope="session", autouse=True)
def login(
    api_request_context: APIRequestContext,
    playwright: Playwright,
):
    login_response = api_request_context.post(
        "/api/auth/login",
        headers=BASE_HEADERS,
        data=json.dumps(
            {
                "username": username,
                "password": password,
            }
        ),
    )
    assert login_response.status == 200
    yield
