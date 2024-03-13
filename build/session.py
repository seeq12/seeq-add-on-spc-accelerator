def get_authenticated_session(
    url: str, project_name: str, username: str, password: str
):
    from seeq import sdk, spy

    spy.login(username=username, password=password, url=url, quiet=True)
    auth_header = {"sq-auth": spy.client.auth_token}
    items_api = sdk.ItemsApi(spy.client)
    response = items_api.search_items(
        filters=[f"name=={project_name}"], types=["Project"]
    )
    if len(response.items) == 0:
        raise Exception(f"Could not find a project with name {project_name}")
    project_id = response.items[0].id
    requests_session = _create_requests_session()
    return requests_session, auth_header, project_id


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
