import pytest
import os
import sys
import json
import time
import types
from seeq import spy
from ao.session import get_project_id_from_name

from ao.ao import (
    PROJECT_PATH,
    _parse_url_username_password,
    get_element_identifier_from_path,
    get_element_config_from_identifier,
)

_url, username, password = _parse_url_username_password()


@pytest.fixture(scope="session")
def url(pytestconfig):
    return _url


@pytest.fixture
def element_identifier(element_path):
    return get_element_identifier_from_path(PROJECT_PATH / element_path)


@pytest.fixture
def project_id(element_identifier):
    return get_project_id_from_name(element_identifier, spy.session)


@pytest.fixture
def element_config(element_identifier):
    return get_element_config_from_identifier(element_identifier)


@pytest.fixture(scope="session")
def api_request_context(url: str, playwright):
    headers = {
        "Accept": "application/vnd.seeq.v1+json",
        "Content-Type": "application/vnd.seeq.v1+json",
        # "sq-auth": spy.client.auth_token,
    }
    request_context = playwright.request.new_context(
        base_url=url, extra_http_headers=headers
    )
    yield request_context
    request_context.dispose()


@pytest.fixture(scope="session", autouse=True)
def login_spy():
    spy.login(username=username, password=password, url=_url, quiet=True)
    assert spy.client.auth_token
    spy.session.options.allow_version_mismatch = True


@pytest.fixture(scope="session", autouse=True)
def login_playwright(
    api_request_context,
    playwright,
):
    login_response = api_request_context.post(
        "/api/auth/login",
        data=json.dumps(
            {
                "username": username,
                "password": password,
            }
        ),
    )
    assert login_response.status == 200
    yield
