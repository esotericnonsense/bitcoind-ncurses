#!/usr/bin/env python
import Queue, textwrap, time

import tx
import monitor
import peers
import wallet
import splash
import console
import net
import forks
import footer

"""
def resize(s, state, window):
    if state['mode'] == 'tx':
        tx.draw_window(state, window)
    elif state['mode'] == 'block':
        block.draw_window(state, window)
    elif state['mode'] == 'peers':
        peers.draw_window(state, window)
    elif state['mode'] == 'wallet':
        wallet.draw_window(state, window)
    elif state['mode'] == 'monitor':
        monitor.draw_window(state, window)
    elif state['mode'] == 'console':
        console.draw_window(state, window)
    elif state['mode'] == 'net':
        net.draw_window(state, window)
"""

def getblockchaininfo(s, state, window):
	if s['getblockchaininfo']['chain'] == "test":
		state['testnet'] = 1
	else:
		state['testnet'] = 0

	if state['mode'] == "splash":
		splash.draw_window(state, window)

def getnetworkinfo(s, state, window):
    state['version'] = s['getnetworkinfo']['subversion']

def getconnectioncount(s, state, window):
    state['peers'] = s['getconnectioncount']

def getbalance(s, state, window):
    state['balance'] = s['getbalance']

def getunconfirmedbalance(s, state, window):
    state['unconfirmedbalance'] = s['getunconfirmedbalance']

def getblock(s, state, window):
    height = s['getblock']['height']

    state['blocks'][str(height)] = s['getblock']

    if state['mode'] == "monitor":
        monitor.draw_window(state, window)
        footer.draw_window(state)

    """
    if state['mode'] == "block":
        # TODO: This query check stops the block view from updating whenever
        #       a new block comes in. It shouldn't fire any more because
        #       we don't poll outside of monitor mode.
        # if 'queried' in s['getblock']:
        if True:
            # state['blocks'][str(height)].pop('queried')
            state['blocks']['browse_height'] = height
            state['blocks']['offset'] = 0
            state['blocks']['cursor'] = 0
            block.draw_window(state, window)
    """

def getblockhash(s, state, window):
    pass

def coinbase(s, state, window):
    height = str(s['height'])
    if height in state['blocks']:
        state['blocks'][height]['coinbase_amount'] = s['coinbase']

def getrawtransaction(s, state, window):
    pass

def getnetworkhashps(s, state, window):
    blocks = s['getnetworkhashps']['blocks']
    state['networkhashps'][blocks] = s['getnetworkhashps']['value']

    if state['mode'] == "splash" and blocks == 2016: # initialization complete
        state['mode'] = "monitor"
        monitor.draw_window(state, window)
        footer.draw_window(state)

def getnettotals(s, state, window):
    state['totalbytesrecv'] = s['getnettotals']['totalbytesrecv']
    state['totalbytessent'] = s['getnettotals']['totalbytessent']

    state['history']['getnettotals'].append(s['getnettotals'])

    # ensure getnettotals history does not fill RAM eventually, 300 items is enough
    if len(state['history']['getnettotals']) > 500:
        state['history']['getnettotals'] = state['history']['getnettotals'][-300:]

    if state['mode'] == 'net':
        net.draw_window(state, window)
        footer.draw_window(state)

def getmininginfo(s, state, window):
    state['mininginfo'] = s['getmininginfo']

    if 'browse_height' not in state['blocks']:
        state['blocks']['browse_height'] = s['getmininginfo']['blocks']

    state['networkhashps']['diff'] = (int(s['getmininginfo']['difficulty'])*2**32)/600

def getpeerinfo(s, state, window):
    state['peerinfo'] = s['getpeerinfo']
    state['peerinfo_offset'] = 0
    if state['mode'] == "peers":
        peers.draw_window(state, window)
        footer.draw_window(state)

def getchaintips(s, state, window):
    state['chaintips'] = s['getchaintips']
    state['chaintips_offset'] = 0
    if state['mode'] == 'forks':
        forks.draw_window(state, window)
        footer.draw_window(state)

def listsinceblock(s, state, window):
    state['wallet'] = s['listsinceblock']
    state['wallet']['cursor'] = 0
    state['wallet']['offset'] = 0

    state['wallet']['view_string'] = []

    state['wallet']['transactions'].sort(key=lambda entry: entry['category'], reverse=True)

    # add cumulative balance field to transactiosn once ordered by time
    state['wallet']['transactions'].sort(key=lambda entry: entry['time'])
    state['wallet']['transactions'].sort(key=lambda entry: entry['confirmations'], reverse=True)
    cumulative_balance = 0
    nonce = 0 # ensures a definitive ordering of transactions for cumulative balance
    for entry in state['wallet']['transactions']:
        entry['nonce'] = nonce
        nonce += 1
        if 'amount' in entry:
            if 'fee' in entry:
                cumulative_balance += entry['fee']
            cumulative_balance += entry['amount']
            entry['cumulative_balance'] = cumulative_balance

    state['wallet']['transactions'].sort(key=lambda entry: entry['nonce'], reverse=True)

    unit = 'BTC'
    if 'testnet' in state:
        if state['testnet']:
            unit = 'TNC'

    for entry in state['wallet']['transactions']:
        if 'txid' in entry:
            entry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(entry['time']))
            output_string = entry_time + " %8d" % entry['confirmations'] + " conf"
            delta = entry['amount']
            if 'fee' in entry:
                delta += entry['fee'] # this fails if not all inputs owned by wallet; could be 'too negative'
            output_string += "% 17.8f" % delta + unit
            output_string += " " + "% 17.8f" % entry['cumulative_balance'] + unit
            state['wallet']['view_string'].append(output_string)

            output_string = entry['txid'].rjust(74)
            state['wallet']['view_string'].append(output_string)

            if 'address' in entry: # TODO: more sanity checking here
                output_string = "          " + entry['category'].ljust(15) + entry['address']
            else:
                output_string = "          unknown transaction type"
            state['wallet']['view_string'].append(output_string)

            state['wallet']['view_string'].append("")

    if state['mode'] == "wallet":
        wallet.draw_window(state, window)
        footer.draw_window(state)

def lastblocktime(s, state, window):
    state['lastblocktime'] = s['lastblocktime']

def txid(s, state, window):
    if s['size'] < 0:
        if 'tx' in state:
            state.pop('tx')
        if state['mode'] == 'tx':
            tx.draw_window(state, window)
            footer.draw_window(state)
        return False

    state['tx'] = {
        'txid': s['txid'],
        'vin': [],
        'vout_string': [],
        'cursor': 0,
        'offset': 0,
        'out_offset': 0,
        'loaded': 1,
        'mode': 'inputs',
        'size': s['size'],
    }

    for vin in s['vin']:
        if 'coinbase' in vin:
            state['tx']['vin'].append({'coinbase':  vin['coinbase']})
        elif 'txid' in vin:
            if 'prev_tx' in vin:
                state['tx']['vin'].append({'txid': vin['txid'], 'vout': vin['vout'], 'prev_tx': vin['prev_tx']})
            else:
                state['tx']['vin'].append({'txid': vin['txid'], 'vout': vin['vout']})

    state['tx']['total_outputs'] = 0
    for vout in s['vout']:
        if 'value' in vout:
            if vout['scriptPubKey']['type'] == "pubkeyhash":
                buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['addresses'][0]
            else:
                buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']

            if 'confirmations' in s:
                if 'spent' in vout:
                    if vout['spent'] == 'confirmed':
                        buffer_string += " [SPENT]"
                    elif vout['spent'] == 'unconfirmed':
                        buffer_string += " [UNCONFIRMED SPEND]"
                    else:
                        buffer_string += " [UNSPENT]"

            state['tx']['total_outputs'] += vout['value']
            state['tx']['vout_string'].extend(textwrap.wrap(buffer_string,70)) # change this to scale with window ?

    if 'total_inputs' in s:
        state['tx']['total_inputs'] = s['total_inputs']

    if 'confirmations' in s:
        state['tx']['confirmations'] = s['confirmations']

    if state['mode'] == 'tx':
        tx.draw_window(state, window)
        footer.draw_window(state)

def consolecommand(s, state, window):
    state['console']['cbuffer'].append(s['consolecommand'])
    state['console']['rbuffer'].append(s['consoleresponse'])
    state['console']['offset'] = 0
    if state['mode'] == "console":
        console.draw_window(state, window)
        footer.draw_window(state)

def estimatefee(s, state, window):
    blocks = s['estimatefee']['blocks']
    state['estimatefee'][blocks] = s['estimatefee']['value']

def queue(state, window, response_queue):
    from rpc2 import RPCResponse
    while True:
        try:
            s = response_queue.get(False)
        except Queue.Empty:
            return False

        if isinstance(s, dict):
            # if 'resize' in s: resize(s, state, window)
            if 'lastblocktime' in s: lastblocktime(s, state, window)
            elif 'txid' in s: txid(s, state, window)
            elif 'consolecommand' in s: consolecommand(s, state, window)
            elif 'coinbase' in s: coinbase(s, state, window)
            elif 'stop' in s: return s['stop']
            continue

        if not isinstance(s, RPCResponse):
            print "Ignoring"
            continue

        methods = {
            "getblockchaininfo": getblockchaininfo,
            "getnetworkinfo": getnetworkinfo,
            "getconnectioncount": getconnectioncount,
            "getbalance": getbalance,
            "getunconfirmedbalance": getunconfirmedbalance,
            "getblock": getblock,
            "getblockhash": getblockhash,
            "getnetworkhashps": getnetworkhashps,
            "getnettotals": getnettotals,
            "getmininginfo": getmininginfo,
            "getpeerinfo": getpeerinfo,
            "getchaintips": getchaintips,
            "getrawtransaction": getrawtransaction,
            "listsinceblock": listsinceblock,
            "estimatefee": estimatefee,
        }

        try:
            method = methods[s.req.method]
        except KeyError:
            print "Unknown {}".format(s.req.method)
            return

        method({s.req.method: s.result}, state, window)
