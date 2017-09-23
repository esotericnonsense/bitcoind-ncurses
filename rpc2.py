import bitcoinrpc.authproxy
import datetime
import gevent.queue
import os
import time
import base64

from collections import namedtuple
class RPCRequest(object):
    def __init__(self, method, *params):
        self.method = method
        self.params = params
        self.uuid = new_uuid()
        self.timestamp = datetime.datetime.utcnow()

class RPCResponse(object):
    def __init__(self, req, result, error=False):
        self.req = req
        self.result = result
        self.error = error
        self.timestamp = datetime.datetime.utcnow()

def new_uuid():
    return base64.b64encode(os.urandom(16))

class BitcoinRPCClient(object):
    def __init__(self, response_queue, block_store, rpcuser, rpcpassword, rpcip="localhost", rpcport=8332, protocol="http", testnet=False):
        rpcurl = "{}://{}:{}@{}:{}".format(
            protocol, rpcuser, rpcpassword, rpcip, rpcport)
        self._handle = bitcoinrpc.authproxy.AuthServiceProxy(rpcurl, None, 500)
        self._request_queue = gevent.queue.Queue()
        self.connected = False

        self._response_queue = response_queue # TODO: refactor this
        self._block_store = block_store

    def _call(self, req):
        assert isinstance(req, RPCRequest)

        # TODO: Does AuthServiceProxy have a time-out? 
        result = getattr(self._handle, req.method)(*req.params)

        return RPCResponse(req, result)

    def connect(self):
        if self.connected:
            return True # Assume it wasn't closed.

        if not self._call(RPCRequest("getblockchaininfo")):
            return False

        self.connected = True
        return True 

    def run(self):
        assert self.connected

        bestheight = None
        bestblockhash = None
        bestcoinbase = None

        for req in self._request_queue:
            resp = self._call(req)

            # TODO: enhackle
            if req.method == "getnetworkhashps" or req.method == "estimatefee":
                resp.result = {
                    "blocks": req.params[0],
                    "value": resp.result,
                }

            elif req.method == "getrawtransaction" and req.params[0] == bestcoinbase:
                coinbase_amount = 0
                for output in resp.result['vout']:
                    if 'value' in output:
                        coinbase_amount += output['value']
                resp2 = {"coinbase": coinbase_amount, "height": bestheight}
                self._response_queue.put(resp2)

            # Enhackerino
            elif req.method == "getrawtransaction":
                try:
                    tx = resp.result
                    tx['size'] = len(tx['hex'])/2

                    if 'coinbase' in tx['vin'][0]: # should always be at least 1 vin
                        tx['total_inputs'] = 'coinbase'

                    # TODO: Implement verbose mode
                    """
                    if 'verbose' in s:
                        tx['total_inputs'] = 0
                        prev_tx = {}
                        for vin in tx['vin']:
                            if 'txid' in vin:
                                try:
                                    txid = vin['txid']
                                    if txid not in prev_tx:
                                        prev_tx[txid] = rpcrequest(rpchandle, 'getrawtransaction', False,
                                                                   txid, 1)

                                    vin['prev_tx'] = prev_tx[txid]['vout'][vin['vout']]
                                    if 'value' in vin['prev_tx']:
                                        tx['total_inputs'] += vin['prev_tx']['value']
                                except:
                                    pass
                            elif 'coinbase' in vin:
                                tx['total_inputs'] = 'coinbase'
                        for vout in tx['vout']:
                            try:
                                utxo = rpcrequest(rpchandle, 'gettxout', False,
                                                    s['txid'], vout['n'], False)
                                if utxo == None:
                                    vout['spent'] = 'confirmed'
                                else:
                                    utxo = rpcrequest(rpchandle, 'gettxout', False,
                                                        s['txid'], vout['n'], True)
                                    if utxo == None:
                                        vout['spent'] = 'unconfirmed'
                                    else:
                                        vout['spent'] = False
                            except:
                                pass
                        """

                except:
                    # TODO: Just use error in resp here
                    tx = {'txid': req.params[0], 'size': -1}

                self._response_queue.put(tx)
                continue

            self._response_queue.put(resp)

            if req.method == "getblockchaininfo":
                new_bestblockhash = resp.result["bestblockhash"]
                if new_bestblockhash != bestblockhash:
                    if not bestblockhash:
                        resp2 = {"lastblocktime" : 0}
                    else:
                        resp2 = {"lastblocktime" : time.time()}
                    bestheight = resp.result["blocks"]
                    bestblockhash = new_bestblockhash

                    # Request the new best block
                    self.request("getblock", bestblockhash)
                    # Request some other information
                    self.request("getnetworkhashps", 144)
                    self.request("getnetworkhashps", 2016)
                    self.request("estimatefee", 2)
                    self.request("estimatefee", 5)

                    self._response_queue.put(resp2)

            elif req.method == "getblock" and req.params[0] == bestblockhash:
                # Request the coinbase
                bestcoinbase = resp.result["tx"][0]
                self.request("getrawtransaction", bestcoinbase, 1)

            elif req.method == "getblockhash":
                self.request("getblock", resp.result)

            if req.method == "getblock":
                self._block_store.put_raw_block(resp.result)

            # TODO: findblockbytimestamp
            # TODO: consolecommand

            # TODO: Remove for production
            with open("test.log", "a") as f:
                f.write("{} RESP {}{}\n".format(resp.timestamp, req.method, req.params))

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
        self._mode = "monitor"

    def run(self):
        self.poll_once(force_all=True)
        while True:
            gevent.sleep(1)
            self.poll_once()

    def poll_once(self, force_all=False):
        if self._mode == "monitor" or force_all:
            self._rpcc.request("getconnectioncount")
            self._rpcc.request("getmininginfo")
            self._rpcc.request("getblockchaininfo")
            self._rpcc.request("getbalance")
            self._rpcc.request("getunconfirmedbalance")

        if self._mode == "peers" or force_all:
            self._rpcc.request("getconnectioncount")
            self._rpcc.request("getpeerinfo")

        if self._mode == "wallet" or force_all:
            self._rpcc.request("listsinceblock")
            self._rpcc.request("getbalance")
            self._rpcc.request("getunconfirmedbalance")

        if force_all:
            self._rpcc.request("getchaintips")

        # Net graph needs to run all the time.
        self._rpcc.request("getnettotals")

    def set_mode(self, mode):
        # TODO: Add a lock here?
        self._mode = mode

if __name__ == "__main__":
    testfn()
