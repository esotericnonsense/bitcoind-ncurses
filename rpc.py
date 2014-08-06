#!/usr/bin/env python
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, Queue, decimal

def stop(interface_queue, error_message):
    interface_queue.put({'stop': error_message})

def init(interface_queue, cfg):
    try:
        rpcuser = cfg.get('rpcuser')
        rpcpassword = cfg.get('rpcpassword')
        rpcip = cfg.get('rpcip', '127.0.0.1')
        if cfg.get('rpcport'):
            rpcport = cfg.get('rpcport')
        elif cfg.get('testnet') == "1":
            rpcport = '18332'
        else:
            rpcport = '8332'

        rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    except:
        stop(interface_queue, "invalid configuration file or missing values")
        return False

    try:
        rpchandle = AuthServiceProxy(rpcurl, None, 500)
        return rpchandle
    except:
        return False

def rpcrequest(rpchandle, request, interface_queue):
    try:
        response = getattr(rpchandle, request)()
        interface_queue.put({request: response})
        return response
    except:
        return False

def getblock(rpchandle, interface_queue, block_to_get, queried = False, new = False):
    try:
        if (len(str(block_to_get)) < 7) and str(block_to_get).isdigit(): 
            blockhash = rpchandle.getblockhash(block_to_get)
        elif len(block_to_get) == 64:
            blockhash = block_to_get

        block = rpchandle.getblock(blockhash)

        if queried:
            block['queried'] = 1

        if new:
            block['new'] = True

        interface_queue.put({'getblock': block})

        return block

    except:
        return 0

def loop(interface_queue, rpc_queue, cfg):
    # TODO: add error checking for broken config, improve exceptions
    rpchandle = init(interface_queue, cfg)
    if not rpchandle: # TODO: this doesn't appear to trigger, investigate
        stop(interface_queue, "failed to connect to bitcoind (handle not obtained)")
        return True

    last_update = time.time() - 2
    
    info = rpcrequest(rpchandle, 'getinfo', interface_queue)
    if not info:
        stop(interface_queue, "failed to connect to bitcoind (getinfo failed)")
        return True

    prev_blockcount = 0
    while True:
        try:
            s = rpc_queue.get(True, 0.1)
        except Queue.Empty:
            s = {}

        if 'stop' in s:
            break

        elif 'consolecommand' in s:
            arguments = s['consolecommand'].split()
            command = arguments[0]
            arguments = arguments[1:]

            # TODO: figure out how to encode properly for submission; this is hacky.
            index = 0
            while index < len(arguments):
                if arguments[index].isdigit():
                    arguments[index] = int(arguments[index])
                elif arguments[index] == "False":
                    arguments[index] = False
                elif arguments[index] == "True":
                    arguments[index] = True
                else:
                    try:
                        arguments[index] = decimal.Decimal(arguments[index])
                    except:
                        pass
                index += 1

            try:
                response = getattr(rpchandle, command)(*arguments)
                interface_queue.put({'consolecommand': s['consolecommand'], 'consoleresponse': response})
            except:
                interface_queue.put({'consolecommand': s['consolecommand'], 'consoleresponse': "ERROR"})

        elif 'getblockhash' in s:
            getblock(rpchandle, interface_queue, s['getblockhash'], True)

        elif 'getblock' in s:
            getblock(rpchandle, interface_queue, s['getblock'], True)

        elif 'txid' in s:
            try:
                tx = rpchandle.getrawtransaction(s['txid'], 1)
                tx['size'] = len(tx['hex'])/2

                if 'coinbase' in tx['vin'][0]: # should always be at least 1 vin
                    tx['total_inputs'] = 'coinbase'

                if 'verbose' in s:
                    tx['total_inputs'] = 0
                    prev_tx = {}
                    for vin in tx['vin']:
                        if 'txid' in vin:
                            try:
                                txid = vin['txid']
                                if txid not in prev_tx:
                                    prev_tx[txid] = rpchandle.getrawtransaction(txid, 1)

                                vin['prev_tx'] = prev_tx[txid]['vout'][vin['vout']]
                                if 'value' in vin['prev_tx']:
                                    tx['total_inputs'] += vin['prev_tx']['value']
                            except:
                                pass
                        elif 'coinbase' in vin:
                            tx['total_inputs'] = 'coinbase'
                    for vout in tx['vout']:
                        try:
                            utxo = rpchandle.gettxout(s['txid'], vout['n'], False)
                            if utxo == None:
                                vout['spent'] = 'confirmed'
                            else:
                                utxo = rpchandle.gettxout(s['txid'], vout['n'], True)
                                if utxo == None:
                                    vout['spent'] = 'unconfirmed'
                                else:
                                    vout['spent'] = False
                        except:
                            pass

            except: 
                tx = {'txid': s['txid'], 'size': -1}

            interface_queue.put(tx)

        elif 'getpeerinfo' in s:
            rpcrequest(rpchandle, 'getpeerinfo', interface_queue)

        elif 'listsinceblock' in s:
            rpcrequest(rpchandle, 'listsinceblock', interface_queue)

        elif 'findblockbytimestamp' in s:
            request = s['findblockbytimestamp']

            # initializing the while loop 
            block_to_try = 0
            delta = 10000 
            iterations = 0
 
            while abs(delta) > 3600 and iterations < 15: # one day
                block = getblock(rpchandle, interface_queue, block_to_try, True)
                if not block:
                    break

                delta = request - block['time']
                block_to_try += int(delta / 600) # guess 10 mins per block. seems to work on testnet anyway 

                if (block_to_try < 0):
                    block = getblock(rpchandle, interface_queue, 0, True)
                    break # assume genesis has earliest timestamp

                elif (block_to_try > blockcount):
                    block = getblock(rpchandle, interface_queue, blockcount, True)
                    break

                iterations += 1

        elif (time.time() - last_update) > 2:
            rpcrequest(rpchandle, 'getnettotals', interface_queue)
            rpcrequest(rpchandle, 'getconnectioncount', interface_queue)
            rpcrequest(rpchandle, 'getrawmempool', interface_queue)
            rpcrequest(rpchandle, 'getbalance', interface_queue)
            rpcrequest(rpchandle, 'getunconfirmedbalance', interface_queue)

            blockcount = rpcrequest(rpchandle, 'getblockcount', interface_queue)
            if blockcount:
                if (prev_blockcount != blockcount): # minimise RPC calls
                    if prev_blockcount == 0:
                        lastblocktime = {'lastblocktime': 0}
                    else:
                        lastblocktime = {'lastblocktime': time.time()}
                    interface_queue.put(lastblocktime)

                    block = getblock(rpchandle, interface_queue, blockcount, False, True)
                    if block:
                        prev_blockcount = blockcount

                        try:
                            raw_tx = rpchandle.getrawtransaction(block['tx'][0])
                            decoded_tx = rpchandle.decoderawtransaction(raw_tx)

                            coinbase_amount = 0
                            for output in decoded_tx['vout']:
                                if 'value' in output:
                                    coinbase_amount += output['value']

                            interface_queue.put({"coinbase": coinbase_amount, "height": blockcount})
                            
                        except: pass 

                    rpcrequest(rpchandle, 'getdifficulty', interface_queue)

                    try:
                        nethash144 = rpchandle.getnetworkhashps(144)
                        nethash2016 = rpchandle.getnetworkhashps(2016)
                        interface_queue.put({'getnetworkhashps': {'blocks': 144, 'value': nethash144}})
                        interface_queue.put({'getnetworkhashps': {'blocks': 2016, 'value': nethash2016}})
                    except: pass

                    try:
                        estimatefee1 = rpchandle.estimatefee(1)
                        estimatefee5 = rpchandle.estimatefee(5)
                        estimatefee = [{'blocks': 1, 'value': estimatefee1}, {'blocks': 5, 'value': estimatefee5}]
                        interface_queue.put({'estimatefee': estimatefee})
                    except: pass

            last_update = time.time()
