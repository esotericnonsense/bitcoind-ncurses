#!/usr/bin/env python
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, Queue 

def init(config):
    rpcuser = config.get('rpc', 'rpcuser')
    rpcpassword = config.get('rpc', 'rpcpassword')
    rpcip = config.get('rpc', 'rpcip')
    rpcport = config.get('rpc', 'rpcport')

    rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    rpchandle = AuthServiceProxy(rpcurl, None, 500)

    return rpchandle

def loop(interface_queue, rpc_queue, config):
    # TODO: add some error checking for failed connection, json error, broken config
    rpchandle = init(config)

    last_update = time.time() - 2

    info = rpchandle.getinfo()
    interface_queue.put({'getinfo': info})

    prev_blockcount = 0
    while 1:
        try: s = rpc_queue.get(False)
        except Queue.Empty: s = {}

        if 'stop' in s:
            break
        elif 'getblockhash' in s:
            blockhash = rpchandle.getblockhash(s['getblockhash'])
            block = rpchandle.getblock(blockhash)
            interface_queue.put({'getblock': block})
        elif 'getblock' in s:
            block = rpchandle.getblock(s['getblock'])
            interface_queue.put({'getblock': block})
        elif 'txid' in s:
            raw_tx = rpchandle.getrawtransaction(s['txid'])
            decoded_tx = rpchandle.decoderawtransaction(raw_tx)
            interface_queue.put(decoded_tx)

        if (time.time() - last_update) > 2:
            nettotals = rpchandle.getnettotals()
            connectioncount = rpchandle.getconnectioncount()
            blockcount = rpchandle.getblockcount()
            balance = rpchandle.getbalance()

            interface_queue.put({'getnettotals' : nettotals})
            interface_queue.put({'getconnectioncount' : connectioncount})
            interface_queue.put({'getblockcount' : blockcount})
            interface_queue.put({'getbalance' : balance})

            if (prev_blockcount != blockcount): # minimise RPC calls
                if prev_blockcount == 0:
                    lastblocktime = {'lastblocktime': 0}
                else:
                    lastblocktime = {'lastblocktime': time.time()}
                interface_queue.put(lastblocktime)

                blockhash = rpchandle.getblockhash(blockcount)
                block = rpchandle.getblock(blockhash)
                interface_queue.put({'getblock': block})

                difficulty = rpchandle.getdifficulty()
                interface_queue.put({'getdifficulty': difficulty})

                nethash144 = rpchandle.getnetworkhashps(144)
                nethash2016 = rpchandle.getnetworkhashps(2016)
                interface_queue.put({'getnetworkhashps': {'blocks': 144, 'value': nethash144}})
                interface_queue.put({'getnetworkhashps': {'blocks': 2016, 'value': nethash2016}})

                prev_blockcount = blockcount

            last_update = time.time()

        time.sleep(0.05) # TODO: investigate a better way to idle CPU
