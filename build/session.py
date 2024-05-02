def get_authenticated_session(
    url: str, project_name: str, username: str, password: str
):
    from seeq import sdk, spy

    spy_session = spy.Session()
    spy.login(
        username=username, password=password, url=url, quiet=True, session=spy_session
    )
    auth_header = {"sq-auth": spy.client.auth_token}
    project_id = get_project_id_from_name(project_name, spy_session)
    requests_session = _create_requests_session()
    return requests_session, auth_header, project_id


def get_project_id_from_name(project_name, session):
    from seeq import sdk

    items_api = sdk.ItemsApi(session.client)
    response = items_api.search_items(
        filters=[f"name=={project_name}"], types=["Project"]
    )
    if len(response.items) == 0:
        raise Exception(f"Could not find a project with name {project_name}")
    return response.items[0].id


def _create_requests_session():
    import requests
    from requests.adapters import HTTPAdapter, Retry

    max_request_retries = 5
    request_retry_status_list = [502, 503, 504]
    _http_adapter = HTTPAdapter(
        max_retries=Retry(
            total=max_request_retries,
            backoff_factor=0.5,
            status_forcelist=request_retry_status_list,
        )
    )
    request_session = requests.Session()
    request_session.mount("http://", _http_adapter)
    request_session.mount("https://", _http_adapter)
    return request_session
