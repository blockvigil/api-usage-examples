import requests
import json
from dynaconf import settings
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpclient
import tornado.escape
from tornado.options import define, options
import logging
import sys

define("port", default=6635, help="run on the given port", type=int)

tornado_logger = logging.getLogger('EIP712ProofLogger')
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


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with, Content-Type")
        self.set_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    def put(self, *args, **kwargs):
        self.set_status(204)
        self.flush()

    def delete(self, *args, **kwargs):
        self.set_status(204)
        self.flush()

    def options(self):
        self.set_status(204)
        self.flush()


class FlatStructHandler(BaseHandler):
    async def post(self):
        request_json = tornado.escape.json_decode(self.request.body)
        tornado_logger.debug(request_json)
        try:
            command = request_json['command']
        except KeyError:
            command = ""
        else:
            contract_address = request_json['contractAddress']
        api_key = settings['ETHVIGIL_API_KEY']
        headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
        if command == 'submitProof':
            # expand the message object into individual components
            msg_obj = list(request_json['messageObject'].values())
            msg_obj_request_str = json.dumps(msg_obj)
            sig_r = request_json['sigR']
            sig_s = request_json['sigS']
            # sig_v = 28
            sig_v = request_json['sigV']

            method_api_endpoint = f'{settings["REST_API_ENDPOINT"]}/contract/{contract_address}/submitProof'
            method_args = {
                '_msg': msg_obj_request_str,
                'sigR': sig_r,
                'sigS': sig_s,
                'sigV': sig_v
            }
            tornado_logger.debug('Sending method args to submitApproval')
            tornado_logger.debug(method_args)
            r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
            tornado_logger.debug(r.text)
            self.set_status(status_code=r.status_code)
            self.write(r.json())
        elif command == 'testVerify':
            method_api_endpoint = f'{settings["REST_API_ENDPOINT"]}/contract/{contract_address}/testVerify'
            tornado_logger.debug(f'Calling testVerify on contract {contract_address}...')
            r = requests.get(url=method_api_endpoint, headers=headers)
            tornado_logger.debug(r.text)
            self.set_status(status_code=r.status_code)
            self.write(r.json())
        else:
            self.set_status(status_code=202)
            self.write({'success': True})


def expand_msgobject(message_obj_map):
    ret_l = list()
    for k in ['actionType', 'timestamp']:
        ret_l.append(message_obj_map[k])
    nested_l = list()
    for k in ['userId', 'wallet']:
        nested_l.append(message_obj_map['authorizer'][k])
    ret_l.append(nested_l)
    return ret_l


class NestedStructHandler(BaseHandler):
    async def post(self):
        # tornado_logger.debug(self.request.headers['content-type'])
        # tornado_logger.debug('---Transaction---')
        tornado_logger.debug(self.request.body)
        request_json = tornado.escape.json_decode(self.request.body)
        # self.set_status(status_code=202)
        # self.write({'success': True})
        command = request_json['command']
        contract_address = request_json['contractAddress']
        api_key = settings['ETHVIGIL_API_KEY']
        headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
        if command == 'submitApproval':
            # expand the message object into individual components
            # msg_obj = ["Action7440", 1570112162, [123, "0x00EAd698A5C3c72D5a28429E9E6D6c076c086997"]]
            # msg_obj_request_str = '["Action7440", 1570112162, [123, "0x00EAd698A5C3c72D5a28429E9E6D6c076c086997"]]'

            # it is necessary to expand the fields according to the order as defined in solidity struct
            # because: the tuple type like (string, uint256, (uint256, address)) is defined according to that order
            msg_obj = expand_msgobject(request_json['messageObject'])
            msg_obj_request_str = json.dumps(msg_obj)
            sig_r = request_json['sigR']
            sig_s = request_json['sigS']
            # sig_v = 28
            sig_v = request_json['sigV']

            method_api_endpoint = f'{settings["REST_API_ENDPOINT"]}/contract/{contract_address}/submitProof'
            method_args = {
                '_msg': msg_obj_request_str,
                'sigR': sig_r,
                'sigS': sig_s,
                'sigV': sig_v
            }
            tornado_logger.debug('Sending method args to submitApproval')
            tornado_logger.debug(method_args)
            r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
            tornado_logger.debug(r.text)
            self.set_status(status_code=r.status_code)
            self.write(r.json())
        elif command == 'testVerify':
            method_api_endpoint = f'{settings["REST_API_ENDPOINT"]}/contract/{contract_address}/testVerify'
            tornado_logger.debug(f'Calling testVerify on contract {contract_address}...')
            r = requests.get(url=method_api_endpoint, headers=headers)
            tornado_logger.debug(r.text)
            self.set_status(status_code=r.status_code)
            self.write(r.json())
        else:
            self.set_status(status_code=202)
            self.write({'success': True})


class WebhookHandler(BaseHandler):
    async def post(self):
        self.set_status(status_code=202)
        self.write({'success': True})
        request_json = tornado.escape.json_decode(self.request.body)
        tornado_logger.debug('*WEBHOOK ENDPOINT*')
        tornado_logger.debug('======Event data payload received======')
        tornado_logger.debug(request_json)


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/flat", FlatStructHandler),
        (r"/webhook", WebhookHandler),
        (r"/nested", NestedStructHandler)

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