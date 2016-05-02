import bitcoinrpc.authproxy
import datetime
import gevent.queue
import os
import base64

from collections import namedtuple
RPCRequest = namedtuple("RPCRequest", ["method", "params", "uuid", "timestamp"])
RPCResponse = namedtuple("RPCResponse", ["method", "result", "error", "uuid", "timestamp"])

def new_uuid():
    return base64.b64encode(os.urandom(16))

class BitcoinRPCClient(object):
    def __init__(self, rpcuser, rpcpassword, rpcip="localhost", rpcport=8332, protocol="http", testnet=False):
        rpcurl = "{}://{}:{}@{}:{}".format(
            protocol, rpcuser, rpcpassword, rpcip, rpcport)
        self._handle = bitcoinrpc.authproxy.AuthServiceProxy(rpcurl, None, 500)
        self._request_queue = gevent.queue.Queue()

    def run(self):
        while True:
            req = self._request_queue.get()
            result = getattr(self._handle, req.method)(*req.params)
            resp = RPCResponse(
                method=req.method,
                result=result,
                error=False, # TODO: Handle errors correctly
                uuid=req.uuid,
                timestamp=datetime.datetime.utcnow(),
            )
            print "{} RESP {} {}".format(resp.timestamp, resp.uuid, resp.method)
            # print resp

    def request(self, method, *params):
        req = RPCRequest(
            method=method,
            params=params,
            uuid=new_uuid(),
            timestamp=datetime.datetime.utcnow(),
        )
        print "{} REQ {} {}".format(req.timestamp, req.uuid, req.method)
        self._request_queue.put(req)

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

if __name__ == "__main__":
    testfn()
