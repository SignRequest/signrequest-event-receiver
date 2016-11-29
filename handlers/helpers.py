"""
    Deals with multipart POST requests.
    The code is adapted from work of Alexis Mignon:
      https://github.com/bryndin/tornado-flickr-api
"""

import mimetypes

import sys
from tornado import httpclient
from tornado import escape
from tornado.httpclient import HTTPRequest


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def safe_bytes(value):
    return escape.utf8(value)


def safe_unicode(value):
    return escape.to_unicode(value)


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value, content_type) elements for data to be
    uploaded as files.
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = b'----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = b'\r\n'
    L = []
    for (key, value) in fields:
        L.append(b'--' + BOUNDARY)
        L.append(b'Content-Disposition: form-data; name="%s"' % safe_bytes(key))
        L.append(b'')
        L.append(safe_bytes(value))
    for (key, filename, value, content_type) in files:
        filename = safe_bytes(filename)
        L.append(b'--' + BOUNDARY)
        L.append(
            b'Content-Disposition: form-data; name="%s"; filename="%s"' % (
                safe_bytes(key), safe_bytes(filename)
            )
        )
        L.append(b'Content-Type: %s' % safe_bytes(content_type or get_content_type(filename)))
        L.append(b'')
        L.append(safe_bytes(value))
    L.append(b'--' + BOUNDARY + b'--')
    L.append(b'')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % safe_unicode(BOUNDARY)
    return content_type, body


async def post_multipart(url, fields, files, extra_request_kwargs=None):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files.
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    extra_request_kwargs = extra_request_kwargs or {}
    headers = extra_request_kwargs.pop('headers', {})
    headers.update({'Content-Type': content_type, 'Content-Length': str(len(body))})
    request_kwargs = extra_request_kwargs
    request_kwargs.update(dict(
        body=body,
        headers=headers
    ))
    request = HTTPRequest(url, "POST", **request_kwargs)
    try:
        return await httpclient.AsyncHTTPClient().fetch(request)
    except httpclient.HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        print("Error: " + str(e), file=sys.stderr)
        print("Url: " + url, file=sys.stderr)
        print("Headers: " + str(e.response.headers), file=sys.stderr)
        print("Body: " + str(e.response.body), file=sys.stderr)
        raise e
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("Error: " + str(e))
        raise e

