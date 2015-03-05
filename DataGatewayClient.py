import json
import datetime
from libhttp import *


class AggressiveEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat(' ')
        elif isinstance(o, datetime.time) or isinstance(o, datetime.date):
            return o.isoformat()
        elif hasattr(o, '__dict__'):
            return o.__dict__
        return json.JSONEncoder.default(self, o)


class DataGatewayJSONRequest(object):
    def __init__(self, key, data, storage):
        self.key = key
        self.data = data
        self.storage = storage

    def getstr(self):
        return json.dumps(self, cls=AggressiveEncoder, encoding='utf-8')


class DataGatewayClient(object):
    def __init__(self, address):
        self._address = address
        self._ios = HTTPIOStream(addr=address)

    def reconnect(self):
        self.close()
        self._ios.open(self._address)

    def close(self):
        self._ios.close()

    def _compose_message(self, key, data, storage):
        req = HTTPRequest(method='PUT')
        req.add(("Content-Type", "application/json"))
        req.body = DataGatewayJSONRequest(key, data, storage).getstr()
        req.add(("Content-Length", len(req.body)))
        return req

    def push(self, key, data, storage):
        self._ios.write_message(self._compose_message(key, data, storage))
        resp = self._ios.read_response()
        return resp.code, resp.body

    def is_connected(self):
        return self._ios.is_open()
