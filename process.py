#!/usr/bin/env python
import Queue, textwrap, time

import tx
import block
import monitor
import peers
import wallet
import splash
import console
import net

def resize(s, state, window):
    if state['mode'] == 'transaction':
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

def getinfo(s, state, window):
    state['version'] = str(s['getinfo']['version'] / 1000000)
    state['version'] += '.' + str((s['getinfo']['version'] % 1000000) / 10000)
    state['version'] += '.' + str((s['getinfo']['version'] % 10000) / 100)
    state['version'] += '.' + str((s['getinfo']['version'] % 100))
    if s['getinfo']['testnet'] == True:
        state['testnet'] = 1
    else:
        state['testnet'] = 0
    state['peers'] = s['getinfo']['connections']

    if 'errors' in s['getinfo']:
        state['errors'] = s['getinfo']['errors']

    if state['mode'] == "splash":
        splash.draw_window(state, window)

def getconnectioncount(s, state, window):
    state['peers'] = s['getconnectioncount']

def getblockcount(s, state, window):
    state['blockcount'] = s['getblockcount']
    if 'browse_height' not in state['blocks']:
        state['blocks']['browse_height'] = state['blockcount']

def getbalance(s, state, window):
    state['balance'] = s['getbalance']

def getunconfirmedbalance(s, state, window):
    state['unconfirmedbalance'] = s['getunconfirmedbalance']

def getblock(s, state, window):
    height = s['getblock']['height']

    state['blocks'][str(height)] = s['getblock']

    if state['mode'] == "monitor":
        monitor.draw_window(state, window)
    if state['mode'] == "block":
        if 'queried' in s['getblock']:
            state['blocks'][str(height)].pop('queried')
            state['blocks']['browse_height'] = height
            state['blocks']['offset'] = 0
            state['blocks']['cursor'] = 0
            block.draw_window(state, window)

def coinbase(s, state, window):
    height = str(s['height'])
    if height in state['blocks']:
        state['blocks'][height]['coinbase_amount'] = s['coinbase']

def getdifficulty(s, state, window):
    state['difficulty'] = s['getdifficulty']

def getnetworkhashps(s, state, window):
    blocks = s['getnetworkhashps']['blocks']
    state['networkhashps'][blocks] = s['getnetworkhashps']['value']

    if state['mode'] == "splash" and blocks == 2016: # initialization complete
        state['mode'] = "monitor"
        monitor.draw_window(state, window)

def getnettotals(s, state, window):
    state['totalbytesrecv'] = s['getnettotals']['totalbytesrecv']
    state['totalbytessent'] = s['getnettotals']['totalbytessent']

    state['history']['getnettotals'].append(s['getnettotals'])

    # ensure getnettotals history does not fill RAM eventually, 300 items is enough
    if len(state['history']['getnettotals']) > 500:
        state['history']['getnettotals'] = state['history']['getnettotals'][-300:]

    if state['mode'] == 'net':
        net.draw_window(state, window)

def getrawmempool(s, state, window):
    state['rawmempool'] = s['getrawmempool']

def getpeerinfo(s, state, window):
    state['peerinfo'] = s['getpeerinfo']
    state['peerinfo_offset'] = 0
    if state['mode'] == "peers":
        peers.draw_window(state, window)

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

def lastblocktime(s, state, window):
    state['lastblocktime'] = s['lastblocktime']

def txid(s, state, window):
    if s['size'] < 0:
        if 'tx' in state:
            state.pop('tx')
        if state['mode'] == "transaction":
            tx.draw_window(state, window)
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

    if state['mode'] == "transaction":
        tx.draw_window(state, window)

def consolecommand(s, state, window):
    state['console']['cbuffer'].append(s['consolecommand'])
    state['console']['rbuffer'].append(s['consoleresponse'])
    state['console']['offset'] = 0
    if state['mode'] == "console":
        console.draw_window(state, window)

def estimatefee(s, state, window):
    state['estimatefee'] = s['estimatefee']

def queue(state, window, interface_queue):
    while True:
        try:
            s = interface_queue.get(False)
        except Queue.Empty:
            return False

        if 'resize' in s: resize(s, state, window)
        elif 'getinfo' in s: getinfo(s, state, window)
        elif 'getconnectioncount' in s: getconnectioncount(s, state, window)
        elif 'getblockcount' in s: getblockcount(s, state, window)
        elif 'getbalance' in s: getbalance(s, state, window)
        elif 'getunconfirmedbalance' in s: getunconfirmedbalance(s, state, window)
        elif 'getblock' in s: getblock(s, state, window)
        elif 'coinbase' in s: coinbase(s, state, window)
        elif 'getdifficulty' in s: getdifficulty(s, state, window)
        elif 'getnetworkhashps' in s: getnetworkhashps(s, state, window)
        elif 'getnettotals' in s: getnettotals(s, state, window)
        elif 'getrawmempool' in s: getrawmempool(s, state, window)
        elif 'getpeerinfo' in s: getpeerinfo(s, state, window)
        elif 'listsinceblock' in s: listsinceblock(s, state, window)
        elif 'lastblocktime' in s: lastblocktime(s, state, window)
        elif 'txid' in s: txid(s, state, window)
        elif 'consolecommand' in s: consolecommand(s, state, window)
        elif 'estimatefee' in s: estimatefee(s, state, window)

        elif 'stop' in s:
            return s['stop']
