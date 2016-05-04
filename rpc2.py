import bitcoinrpc.authproxy
import datetime
import gevent.queue
import os
import time
import base64

import rpc

from collections import namedtuple
class RPCRequest(object):
    def __init__(self, method, *params):
        self.method = method
        self.params = params
        self.uuid = new_uuid()
        self.timestamp = datetime.datetime.utcnow()

class RPCResponse(object):
    def __init__(self, req, result, error=False):
        self.method = req.method
        self.result = result
        self.error = error
        self.uuid = req.uuid
        self.timestamp = datetime.datetime.utcnow()

def new_uuid():
    return base64.b64encode(os.urandom(16))

class BitcoinRPCClient(object):
    def __init__(self, response_queue, rpcuser, rpcpassword, rpcip="localhost", rpcport=8332, protocol="http", testnet=False):
        rpcurl = "{}://{}:{}@{}:{}".format(
            protocol, rpcuser, rpcpassword, rpcip, rpcport)
        self._handle = bitcoinrpc.authproxy.AuthServiceProxy(rpcurl, None, 500)
        self._request_queue = gevent.queue.Queue()
        self.connected = False

        self._response_queue = response_queue # TODO: refactor this

    def _call(self, req):
        assert isinstance(req, RPCRequest)

        # TODO: Does AuthServiceProxy have a time-out? 
        result = getattr(self._handle, req.method)(*req.params)

        return RPCResponse(req, result)

    def connect(self):
        if self.connected:
            return True # Assume it wasn't closed.

        if not self._call(RPCRequest("getinfo")): 
            return False

        self.connected = True
        return True 

    def run(self):
        assert self.connected

        bestblockhash = None

        for req in self._request_queue:
            resp = self._call(req)

            # TODO: debug
            # print "{} RESP {} {}".format(resp.timestamp, resp.uuid, resp.method)

            # TODO: enhackle
            if req.method == "getnetworkhashps":
                resp.result = {
                    "blocks": req.params[0],
                    "value": resp.result,
                }

            self._response_queue.put(resp)

            if req.method == "getblockchaininfo":
                new_bestblockhash = resp.result["bestblockhash"]
                if new_bestblockhash != bestblockhash:
                    if not bestblockhash:
                        resp2 = {"lastblocktime" : 0}
                    else:
                        resp2 = {"lastblocktime" : time.time()}
                    bestblockhash = new_bestblockhash

                    # Request the new best block
                    self._request_queue.put(RPCRequest("getblock", bestblockhash))

                    self._response_queue.put(resp2)

    def request(self, method, *params):
        """ Asynchronous RPC request. """
        req = RPCRequest(method, *params)
        self._request_queue.put(req)

    def sync_request(self, method, *params):
        """ Synchronous RPC request. """
        req = RPCRequest(method, *params)
        return self._call(req)

    def stop(self):
        self._request_queue.put(StopIteration)

def testfn():
    import config
    cfg = config.read_file("bitcoin.conf")

    rpcc = BitcoinRPCClient(
        rpcuser=cfg["rpcuser"],
        rpcpassword=cfg["rpcpassword"],
    )

    gevent.spawn(rpcc.run)

    while True:
        for i in xrange(10):
            rpcc.request("getblockchaininfo")
        print
        gevent.sleep(2)
        print

class Poller(object):
    def __init__(self, rpcc):
        self._rpcc = rpcc

    def run(self):
        while True:
            self._rpcc.request("getnettotals")
            self._rpcc.request("getconnectioncount")
            self._rpcc.request("getmininginfo")
            self._rpcc.request("getblockchaininfo")
            self._rpcc.request("getbalance")
            self._rpcc.request("getunconfirmedbalance")
            self._rpcc.request("getnetworkhashps", 144)
            self._rpcc.request("getnetworkhashps", 2016)

            gevent.sleep(1)

if __name__ == "__main__":
    testfn()
