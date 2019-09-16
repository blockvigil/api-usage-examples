import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpclient
import tornado.escape
from tornado.options import define, options
import logging
import sys

define("port", default=5554, help="run on the given port", type=int)

tornado_logger = logging.getLogger('WebhookListener')
tornado_logger.propagate = False
tornado_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(u"%(levelname)-8s %(name)-4s %(asctime)s,%(msecs)d %(module)s-%(funcName)s: %(message)s")

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)
stderr_handler.setFormatter(formatter)

tornado_logger.addHandler(stdout_handler)
tornado_logger.addHandler(stderr_handler)

hn = logging.NullHandler()
hn.setLevel(logging.DEBUG)
logging.getLogger("tornado.access").addHandler(hn)
logging.getLogger("tornado.access").propagate = False


class MainHandler(tornado.web.RequestHandler):
    async def post(self):
        # tornado_logger.debug(self.request.headers['content-type'])
        # tornado_logger.debug('---Transaction---')
        request_json = tornado.escape.json_decode(self.request.body)
        self.set_status(status_code=202)
        self.write({'success': True})
        if 'event_name' in request_json:
            tornado_logger.debug('========New event received========')
            tornado_logger.debug(request_json['event_name'])
            tornado_logger.debug('---JSON Payload delivered-----')
            tornado_logger.debug(request_json)


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler),

    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado_logger.debug('Shutting down...')
        tornado.ioloop.IOLoop.current().stop()


if __name__ == '__main__':
    main()