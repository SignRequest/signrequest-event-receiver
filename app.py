import os
import sys
import tornado.ioloop
import tornado.web
import tornado.escape
from handlers import MainHandler, BambooHRHandler
from tornado.log import enable_pretty_logging

enable_pretty_logging()


def make_app(debug=False):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/bamboohr", BambooHRHandler),
    ], debug=debug)


if __name__ == "__main__":
    app = make_app(debug=os.environ.get('SR_RECEIVER_DEBUG', False))
    port = os.environ.get('SR_RECEIVER_PORT', 8888)
    app.listen(port)
    print('Starting web server on port', port, file=sys.stdout)
    tornado.ioloop.IOLoop.current().start()
