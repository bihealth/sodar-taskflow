"""API for accessing the Django Taskflow REST service"""

import requests


class OmicsRequestException(Exception):
    """General django REST API submission exception"""
    pass


class OmicsAPI:
    """API for accessing the Django Taskflow REST views"""

    def __init__(self, omics_url):
        self.omics_url = omics_url

    def send_request(self, url, query_data):
        request_url = self.omics_url + '/' + url
        response = requests.post(request_url, data=query_data)

        if response.status_code != 200:
            raise OmicsRequestException(response.text)

        return response
