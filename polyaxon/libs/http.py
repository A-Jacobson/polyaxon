import os
import requests
import tarfile

from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from rest_framework.authentication import TokenAuthentication

from django.conf import settings

from libs.api import get_service_api_url
from libs.permissions.authentication import InternalAuthentication


def absolute_uri(url):
    if not url or not settings.API_HOST:
        return None

    return urljoin(settings.API_HOST.rstrip('/') + '/', url.lstrip('/'))


def add_notification_referrer_param(url, provider, is_absolute=True):
    if not is_absolute:
        url = absolute_uri(url)
    if not url:
        return None
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    query['referrer'] = provider
    url_list = list(parsed_url)
    url_list[4] = urlencode(query, doseq=True)
    return urlunparse(url_list)


def validate_url(url):
    if not url.startswith(('http://', 'https://')):
        return False
    parsed = urlparse(url)
    if not parsed.hostname:
        return False
    return True


def safe_request(
    url,
    method=None,
    params=None,
    data=None,
    json=None,
    headers=None,
    allow_redirects=False,
    timeout=30,
    verify_ssl=True,
):
    """A slightly safer version of `request`."""

    session = requests.Session()

    kwargs = {}

    if json:
        kwargs['json'] = json
        if not headers:
            headers = {}
        headers.setdefault('Content-Type', 'application/json')

    if data:
        kwargs['data'] = data

    if params:
        kwargs['params'] = params

    if headers:
        kwargs['headers'] = headers

    if method is None:
        method = 'POST' if (data or json) else 'GET'

    response = session.request(
        method=method,
        url=url,
        allow_redirects=allow_redirects,
        timeout=timeout,
        verify=verify_ssl,
        **kwargs
    )

    return response


def download(url,
             filename,
             logger,
             authentication_type=None,
             access_token=None,
             headers=None,
             timeout=60):
    """Download the file from the given url at the current path"""
    authentication_type = authentication_type or InternalAuthentication.keyword
    if authentication_type == InternalAuthentication.keyword and not access_token:
        access_token = settings.INTERNAL_SECRET_TOKEN
    elif authentication_type == TokenAuthentication.keyword and not access_token:
        raise ValueError('Access token is required')

    # Auth headers if access_token is present
    request_headers = {}
    if access_token:
        request_headers["Authorization"] = "{} {}".format(authentication_type, access_token)
    # Add any additional headers
    if headers:
        request_headers.update(headers)

    try:
        api_url = get_service_api_url()
        url = '{}/{}'.format(api_url, url)
        logger.info("Downloading file from %s using %s" % (url, authentication_type))
        response = requests.get(url,
                                headers=request_headers,
                                timeout=timeout,
                                stream=True)

        if response.status_code != 200:
            logger.warning("Failed to download file from %s: %s" % (url, response.status_code))
            return None

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return filename

    except requests.exceptions.RequestException as e:
        logger.warning("Exception: %s" % e)
        return None


def untar_file(build_path, filename, logger, delete_tar=False):
    if filename:
        logger.info("Untarring the contents of the file ...")
        tar = tarfile.open(filename)
        tar.extractall(build_path)
        tar.close()
    if delete_tar:
        logger.info("Cleaning up the tar file ...")
        os.remove(filename)
    return filename
