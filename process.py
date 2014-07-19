#!/usr/bin/env python
import Queue, textwrap, time

import tx
import block
import monitor
import peers
import wallet

def queue(state, window, interface_queue):
    try: s = interface_queue.get(False)
    except Queue.Empty: s = {}

    if 'stop' in s:
        return s['stop']

    if 'resize' in s:
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
        # redraw_all_the_things
        pass

    if 'getinfo' in s:
        state['version'] = str(s['getinfo']['version'] / 1000000)
        state['version'] += '.' + str((s['getinfo']['version'] % 1000000) / 10000)
        state['version'] += '.' + str((s['getinfo']['version'] % 10000) / 100)
        state['version'] += '.' + str((s['getinfo']['version'] % 100))
        if s['getinfo']['testnet'] == True:
            state['testnet'] = 1
        else:
            state['testnet'] = 0
        state['peers'] = s['getinfo']['connections']
    
    elif 'getconnectioncount' in s:
        state['peers'] = s['getconnectioncount']

    elif 'getblockcount' in s:
        state['blockcount'] = s['getblockcount']
        if 'browse_height' not in state['blocks']:
            state['blocks']['browse_height'] = state['blockcount']

    elif 'getbalance' in s:
        state['balance'] = s['getbalance']

    elif 'getunconfirmedbalance' in s:
        state['unconfirmedbalance'] = s['getunconfirmedbalance']

    elif 'getblock' in s:
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

    elif 'coinbase' in s:
        height = str(s['height'])
        if height in state['blocks']:
            state['blocks'][height]['coinbase_amount'] = s['coinbase']

    elif 'getdifficulty' in s:
        state['difficulty'] = s['getdifficulty']

    elif 'getnetworkhashps' in s:
        blocks = s['getnetworkhashps']['blocks']
        state['networkhashps'][blocks] = s['getnetworkhashps']['value']

    elif 'getnettotals' in s:
        state['totalbytesrecv'] = s['getnettotals']['totalbytesrecv']
        state['totalbytessent'] = s['getnettotals']['totalbytessent']

    elif 'getrawmempool' in s:
        state['rawmempool'] = s['getrawmempool']

    elif 'getpeerinfo' in s:
        state['peerinfo'] = s['getpeerinfo']
        state['peerinfo_offset'] = 0
        if state['mode'] == "peers":
            peers.draw_window(state, window)

    elif 'listsinceblock' in s:
        state['wallet'] = s['listsinceblock']
        state['wallet']['cursor'] = 0
        state['wallet']['offset'] = 0

        state['wallet']['view_string'] = []

        state['wallet']['transactions'].sort(key=lambda entry: entry['category'], reverse=True)

        # add cumulative balance field to transactiosn once ordered by time
        state['wallet']['transactions'].sort(key=lambda entry: entry['time'])
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

        for entry in state['wallet']['transactions']: 
            if 'txid' in entry:
                entry_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(entry['time']))
                output_string = entry_time + " %8d" % entry['confirmations'] + " conf"
                delta = entry['amount']
                if 'fee' in entry:
                    delta += entry['fee']
                output_string +=  "% 17.8f" % delta + "BTC "
                output_string +=  "% 17.8f" % entry['cumulative_balance'] + "BTC"
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

    elif 'lastblocktime' in s:
        state['lastblocktime'] = s['lastblocktime']

    elif 'txid' in s:
        state['tx'] = {
            'txid': s['txid'],
            'vin': [],
            'vout_string': [],
            'cursor': 0,
            'offset': 0,
            'out_offset': 0,
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
                state['tx']['total_outputs'] += vout['value']
                state['tx']['vout_string'].extend(textwrap.wrap(buffer_string,70)) # change this to scale with window ?

        if 'total_inputs' in s:
            state['tx']['total_inputs'] = s['total_inputs']

        if 'confirmations' in s:
            state['tx']['confirmations'] = s['confirmations']

        if state['mode'] == "transaction":
            tx.draw_window(state, window)

    return False
