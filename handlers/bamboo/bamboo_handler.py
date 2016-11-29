import cgi
import os

import sys

from tornado import httpclient, escape, gen

from handlers import MainHandler
from handlers.helpers import post_multipart, get_content_type


class ImproperlyConfigured(Exception):
    pass


class BambooHRClient(object):

    def __init__(self,
                 bamboo_token=os.environ.get('BAMBOO_TOKEN'),
                 bamboo_subdomain=os.environ.get('BAMBOO_SUBDOMAIN'),
                 file_category_id=os.environ.get('BAMBOO_FILE_CATEGORY_ID', '2'),
                 share_with_employee=os.environ.get('BAMBOO_SHARE_WITH_EMPLOYEE', None)):
        if not all([bamboo_token, bamboo_subdomain]):
            pass
            # raise ImproperlyConfigured(
            #     'The following environment variables are required: '
            #     'BAMBOO_TOKEN, BAMBOO_SUBDOMAIN, BAMBOO_FILE_CATEGORY_ID'
            # )
        self.bamboo_token = bamboo_token
        self.bamboo_subdomain = bamboo_subdomain
        self.file_category_id = file_category_id
        self.share_with_employee = 'no' if share_with_employee in [None, 0, '0', False] else 'yes'
        self.bamboo_api = 'https://api.bamboohr.com/api/gateway.php/{}'.format(self.bamboo_subdomain)

    def get_request_kwargs(self):
        return dict(follow_redirects=True,
                    request_timeout=20.0)

    def get_bamboo_request_kwargs(self):
        kwargs = self.get_request_kwargs()
        kwargs.update(dict(auth_username=self.bamboo_token,
                           auth_password=None,
                           headers={'Accept': 'application/json'}
                           ))
        return kwargs

    async def fetch(self, *args, **kwargs):
        return await httpclient.AsyncHTTPClient().fetch(*args, **kwargs)

    async def fetch_file(self, url):
        pdf_file_resp = await self.fetch(url)
        file_name = None
        if pdf_file_resp.headers.get('Content-Disposition'):
            file_name = cgi.parse_header(pdf_file_resp.headers['Content-Disposition'])[1].get('filename', None)
        file_name = file_name or os.path.basename(url).split('?', 1)[0]
        file_content_type = pdf_file_resp.headers.get('Content-Type') or get_content_type(file_name)
        return {'content': pdf_file_resp.body, 'content_type': file_content_type, 'file_name': file_name}

    async def post_file_to_bamboo(self, file_data, pretty_name, bamboo_employee_id):
        # create files in bamboo
        files = [('file', file_data['file_name'], file_data['content'], file_data['content_type'])]
        fields = [
            ('fileName', pretty_name),
            ('share', self.share_with_employee),
            ('category', self.file_category_id)
        ]
        return await post_multipart(
            '{}/v1/employees/{}/files/'.format(self.bamboo_api, bamboo_employee_id),
            fields,
            files,
            extra_request_kwargs=self.get_bamboo_request_kwargs(),
        )

    async def get_bamboo_employee_mapping(self):
        """
        Fetches the employee {email: bamboo_id} mapping of BambooHR needed to upload files to this employee
        :return: email, ID mapping
        :rtype: dict
        """
        response = await self.fetch(
            '{}/v1/employees/directory'.format(self.bamboo_api), **self.get_bamboo_request_kwargs()
        )
        json_data = escape.json_decode(response.body)
        bamboo_employee_map = {x['workEmail']: x['id'] for x in json_data['employees']}
        return bamboo_employee_map


class BambooHRHandler(MainHandler):

    async def handle_event(self, event_data):
        if event_data['event_type'] == 'signed':  # only do something on the document `signed` event
            bamboo_client = BambooHRClient()

            pdf_url = event_data['document']['pdf']
            signing_log = event_data['document']['signing_log'] or {}
            signing_log_url = signing_log.get('pdf', None)
            # async fetch the pdf files and the bamboo employee mapping
            pdf_file_data, signing_log_file_data, bamboo_employee_mapping = await gen.multi([
                bamboo_client.fetch_file(pdf_url),
                bamboo_client.fetch_file(signing_log_url),
                bamboo_client.get_bamboo_employee_mapping()
            ])

            pdf_pretty_name = event_data['document']['name']
            signing_log_pretty_name = signing_log_file_data['file_name']

            sender_email = event_data['document']['signrequest']['from_email']

            for signer in event_data['document']['signrequest']['signers']:
                if not signer['needs_to_sign']:
                    # they didn't sign so don't upload to bamboo
                    continue
                if signer['email'] == sender_email:
                    # never upload to the sender (employee) of the signrequest
                    continue
                if not signer['signed']:
                    # they might have declined here, in which case we also don't want to upload to bamboo
                    continue
                bamboo_employee_id = bamboo_employee_mapping.get(signer['email'], None)
                if not bamboo_employee_id:
                    print('Bamboo employee ID not found for email: ', signer['email'], file=sys.stderr)
                    continue

                # async upload the signed document and signing log to the employee in BambooHR
                await gen.multi([
                    bamboo_client.post_file_to_bamboo(pdf_file_data, pdf_pretty_name,
                                                      bamboo_employee_id),
                    bamboo_client.post_file_to_bamboo(signing_log_file_data, signing_log_pretty_name,
                                                      bamboo_employee_id)
                ])
