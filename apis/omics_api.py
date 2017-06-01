"""API for accessing the Django Taskflow REST service"""

import requests


class OmicsRequestException(Exception):
    """General django REST API submission exception"""
    pass


class OmicsAPI:
    """API for accessing the Django Taskflow REST service"""

    def __init__(self, django_host, django_port):
        self.omics_url = 'http://{}:{}/taskflow'.format(
            django_host, django_port)

    def retrieve(self, obj_type, obj_pk, query_params=None):
        url = self.omics_url + '/{}/{}'.format(obj_type, obj_pk)
        response = requests.get(url, query_params)

        if response.status_code != 200:
            raise OmicsRequestException(response.text)

        return response

    def find(self, obj_type, query_data):
        url = self.omics_url + '/{}/find'.format(obj_type)
        response = requests.post(url, data=query_data)

        if response.status_code != 200:
            raise OmicsRequestException(response.text)

        return response

    def update(self, obj_type, obj_pk, data):
        url = self.omics_url + '/{}/{}/update'.format(obj_type, obj_pk)
        response = requests.post(url, data)

        if response.status_code != 200:
            raise OmicsRequestException(response.text)

        return True

    def set(self, obj_type, data):
        url = self.omics_url + '/{}/set'.format(obj_type)
        response = requests.post(url, data)

        if response.status_code != 200:
            raise OmicsRequestException(response.text)

        return response

    def remove(self, obj_type, data):
        url = self.omics_url + '/{}/remove'.format(obj_type)
        response = requests.post(url, data)

        if response.status_code != 200:
            raise OmicsRequestException(response.text)

        return response
