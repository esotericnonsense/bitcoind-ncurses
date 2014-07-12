#!/usr/bin/env python
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, Queue 

def stop(interface_queue, error_message):
    interface_queue.put({'stop': error_message})

def init(config):
    rpcuser = config.get('rpc', 'rpcuser')
    rpcpassword = config.get('rpc', 'rpcpassword')
    rpcip = config.get('rpc', 'rpcip')
    rpcport = config.get('rpc', 'rpcport')

    rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    try:
        rpchandle = AuthServiceProxy(rpcurl, None, 500)
        return rpchandle
    except:
        return False

def getblock(rpchandle, interface_queue, block_to_get, queried = False):
    try:
        if (len(str(block_to_get)) < 7) and str(block_to_get).isdigit(): 
            blockhash = rpchandle.getblockhash(block_to_get)
        elif len(block_to_get) == 64:
            blockhash = block_to_get

        block = rpchandle.getblock(blockhash)

        if queried:
            block['queried'] = 1

        interface_queue.put({'getblock': block})

        return block

    except:
        return 0

def loop(interface_queue, rpc_queue, config):
    # TODO: add error checking for broken config, improve exceptions
    rpchandle = init(config)
    if not rpchandle: # TODO: this doesn't appear to trigger, investigate
        stop(interface_queue, "failed to connect to bitcoind")
        return True

    last_update = time.time() - 2
    
    try:
        info = rpchandle.getinfo()
        interface_queue.put({'getinfo': info})
    except:
        stop(interface_queue, "first getinfo failed")
        return True

    prev_blockcount = 0
    while True:
        try:
            s = rpc_queue.get(False)
        except Queue.Empty:
            s = {}

        if 'stop' in s:
            break

        elif 'getblockhash' in s:
            getblock(rpchandle, interface_queue, s['getblockhash'], True)

        elif 'getblock' in s:
            getblock(rpchandle, interface_queue, s['getblock'], True)

        elif 'txid' in s:
            try:
                raw_tx = rpchandle.getrawtransaction(s['txid'])
                decoded_tx = rpchandle.decoderawtransaction(raw_tx)
                decoded_tx['size'] = len(raw_tx)/2
                interface_queue.put(decoded_tx)
            except: 
                stop(interface_queue, "getrawtransaction failed. consider running with -txindex")
                return True

        elif 'getpeerinfo' in s:
            try:
                peerinfo = rpchandle.getpeerinfo()
                interface_queue.put({'getpeerinfo': peerinfo})
            except: pass

        elif 'listsinceblock' in s:
            try:
                sinceblock = rpchandle.listsinceblock()
                interface_queue.put({'listsinceblock': sinceblock})
            except: pass

        elif 'findblockbytimestamp' in s:
            request = s['findblockbytimestamp']

            block_to_try = 0
            delta = 10000 
            iterations = 0
 
            while abs(delta) > 3600 and iterations < 15: # one day
                block = getblock(rpchandle, interface_queue, block_to_try, True)
                if not block:
                    break

                iterations += 1

                delta = request - block['time']
                block_to_try += int(delta / 600) # guess 10 mins per block. seems to work on testnet anyway 

                if (block_to_try < 0):
                    block = getblock(rpchandle, interface_queue, 0, True)
                    break # assume genesis has earliest timestamp

                elif (block_to_try > blockcount):
                    block = getblock(rpchandle, interface_queue, blockcount, True)
                    break

        if (time.time() - last_update) > 2:
            try:
                nettotals = rpchandle.getnettotals()
                connectioncount = rpchandle.getconnectioncount()
                blockcount = rpchandle.getblockcount()
                rawmempool = rpchandle.getrawmempool()

                interface_queue.put({'getnettotals' : nettotals})
                interface_queue.put({'getconnectioncount' : connectioncount})
                interface_queue.put({'getblockcount' : blockcount})
                interface_queue.put({'getrawmempool' : rawmempool})
            except: pass

            try:
                balance = rpchandle.getbalance()
                unconfirmedbalance = rpchandle.getunconfirmedbalance()
                interface_queue.put({'getbalance' : balance})
                interface_queue.put({'getunconfirmedbalance' : unconfirmedbalance})
            except: pass

            if (prev_blockcount != blockcount): # minimise RPC calls
                if prev_blockcount == 0:
                    lastblocktime = {'lastblocktime': 0}
                else:
                    lastblocktime = {'lastblocktime': time.time()}
                interface_queue.put(lastblocktime)

                block = getblock(rpchandle, interface_queue, blockcount)
                if block:
                    prev_blockcount = blockcount

                try:
                    difficulty = rpchandle.getdifficulty()
                    interface_queue.put({'getdifficulty': difficulty})
                except: pass

                try:
                    nethash144 = rpchandle.getnetworkhashps(144)
                    nethash2016 = rpchandle.getnetworkhashps(2016)
                    interface_queue.put({'getnetworkhashps': {'blocks': 144, 'value': nethash144}})
                    interface_queue.put({'getnetworkhashps': {'blocks': 2016, 'value': nethash2016}})
                except: pass


            last_update = time.time()

        time.sleep(0.05) # TODO: investigate a better way to idle CPU
