"""API for accessing the Django Taskflow REST service"""

import requests


TL_URL = 'timeline/taskflow/status/set'
ZONE_URL = 'zones/taskflow/status/set'


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
            raise OmicsRequestException(
                '{}: {}'.format(
                    response.status_code, response.text or 'Unknown'))

        return response

    def set_timeline_status(
            self, event_pk, status_type, status_desc=None, extra_data=None):
        set_data = {
            'event_pk': event_pk,
            'status_type': status_type,
            'status_desc': status_desc,
            'extra_data': extra_data}
        self.send_request(TL_URL, set_data)
