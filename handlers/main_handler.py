import hashlib
import hmac
import os
import sys
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.httpclient


SIGNREQUEST_TOKEN = os.environ.get('SIGNREQUEST_TOKEN', '')

tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

class MainHandler(tornado.web.RequestHandler):

    async def handle_event(self, event_data):
        raise NotImplementedError('Override `MainHandler.handle_event()`!')

    @staticmethod
    def confirm_callback_authenticity(event_data):
        event_time, event_type, event_hash = event_data.get('event_time'), event_data.get('event_type'), event_data.get(
            'event_hash')
        if not all([event_time, event_type, event_hash]):
            return False
        return event_hash == hmac.new(bytes(SIGNREQUEST_TOKEN, encoding='UTF-8'), bytes(event_time + event_type,
                                                                                        encoding='UTF-8'),
                                      hashlib.sha256).hexdigest()

    def get(self):
        self.write("Hello! The server is running!")

    def post(self, *args, **kwargs):
        event_data = tornado.escape.json_decode(self.request.body)
        if self.confirm_callback_authenticity(event_data):
            tornado.ioloop.IOLoop.current().spawn_callback(self.handle_event, event_data)
            self.write("OK")
        else:
            self.set_status(401)
            self.write("ERROR")
        self.finish()
