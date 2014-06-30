#!/usr/bin/env python
import curses, Queue, textwrap 

import tx
import block
import monitor

def user_input(state, window, rpc_queue):
    c = window.getch()

    if c == ord('q') or c == ord('Q'):
        return True

    if c == ord('m') or c == ord('M'):
        state['mode'] = "monitor"
        monitor.draw_window(state, window)

    if c == ord('t') or c == ord('T'):
        state['mode'] = "transaction"
        tx.draw_window(state, window)

    if c == ord('g') or c == ord('G'):
        if state['mode'] == "transaction":
            state['mode'] = "transaction-input"
            tx.draw_input_window(state, window, rpc_queue)
        elif state['mode'] == "block":
            state['mode'] = "block-input"
            block.draw_input_window(state, window, rpc_queue)

    if c == ord('b') or c == ord('B'):
        state['mode'] = "block"
        block.draw_window(state, window)

    if c == ord('l') or c == ord('L'):
        if state['mode'] == "block":
            if 'blockcount' in state:
                state['blocks']['browse_height'] = state['blockcount']
                if 'browse_height' not in state['blocks']:
                    s = {'getblockhash': state['blocks']['browse_height']}
                    rpc_queue.put(s)
                else:
                    block.draw_window(state, window)

    if c == curses.KEY_DOWN:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] < (len(state['tx']['vin']) - 1):
                    state['tx']['cursor'] += 1
                    if (state['tx']['cursor'] - state['tx']['offset']) > 6:
                        state['tx']['offset'] += 1
                    tx.draw_inputs(state)

        elif state['mode'] == "block":
            if 'blocks' in state:
                height = str(state['blocks']['browse_height'])
                blockdata = state['blocks'][height]
                if state['blocks']['cursor'] < (len(blockdata['tx']) - 1):
                    state['blocks']['cursor'] += 1
                    if (state['blocks']['cursor'] - state['blocks']['offset']) > 14:
                        state['blocks']['offset'] += 1
                    block.draw_transactions(state)

    if c == curses.KEY_UP:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] > 0:
                    if (state['tx']['cursor'] - state['tx']['offset']) == 0:
                        state['tx']['offset'] -= 1
                    state['tx']['cursor'] -= 1
                    tx.draw_inputs(state)

        elif state['mode'] == "block":
            if 'blocks' in state:
                if state['blocks']['cursor'] > 0:
                    if (state['blocks']['cursor'] - state['blocks']['offset']) == 0:
                        state['blocks']['offset'] -= 1
                    state['blocks']['cursor'] -= 1
                    block.draw_transactions(state)

    if c == curses.KEY_PPAGE:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['out_offset'] > 1:
                    state['tx']['out_offset'] -= 2
                    tx.draw_outputs(state)

    if c == curses.KEY_NPAGE:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['out_offset'] < (len(state['tx']['vout_string']) - 7):
                    state['tx']['out_offset'] += 2
                    tx.draw_outputs(state)

    if c == ord(' '):
        # TODO: some sort of indicator that a transaction is loading
        if state['mode'] == "transaction":
            if 'tx' in state:
                if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]: 
                    s = {'txid': state['tx']['vin'][ state['tx']['cursor'] ]['txid']}
                    rpc_queue.put(s)

        if state['mode'] == "block":
            if 'blocks' in state:
                if state['blocks']['browse_height'] > 0: # block 0 is not indexed
                    height = str(state['blocks']['browse_height'])
                    if height in state['blocks']:
                        blockdata = state['blocks'][height]
                        s = {'txid': blockdata['tx'][ state['blocks']['cursor'] ]}
                        rpc_queue.put(s)
                        state['mode'] = "transaction"

    if c == curses.KEY_LEFT:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) > 0:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] -= 1
                        if state['blocks']['browse_height'] in state['blocks']:
                            block.draw_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    if c == curses.KEY_RIGHT:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) < state['blockcount']:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] += 1
                        if state['blocks']['browse_height'] in state['blocks']:
                            block.draw_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    return False

def queue(state, window, interface_queue):
    try: s = interface_queue.get(False)
    except Queue.Empty: s = {}

    if 'stop' in s:
        return s['stop']

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

    elif 'getblockcount' in s:
        state['blockcount'] = s['getblockcount']
        if 'browse_height' not in state['blocks']:
            state['blocks']['browse_height'] = state['blockcount']

    elif 'getbalance' in s:
        state['balance'] = s['getbalance']

    elif 'getblock' in s:
        height = s['getblock']['height']

        state['blocks'][str(height)] = s['getblock']
        state['blocks']['cursor'] = 0
        state['blocks']['offset'] = 0

        if state['mode'] == "monitor":
            monitor.draw_window(state, window)
        if state['mode'] == "block":
            if 'queried_block' in state['blocks']:
                if s['getblock']['hash'] == state['blocks']['queried_block']:
                    state['blocks'].pop('queried_block')
                    state['blocks']['browse_height'] = height
            block.draw_window(state, window)

    elif 'getdifficulty' in s:
        state['difficulty'] = s['getdifficulty']

    elif 'getnetworkhashps' in s:
        blocks = s['getnetworkhashps']['blocks']
        state['networkhashps'][blocks] = s['getnetworkhashps']['value']

    elif 'getnettotals' in s:
        state['totalbytesrecv'] = s['getnettotals']['totalbytesrecv']
        state['totalbytessent'] = s['getnettotals']['totalbytessent']

    elif 'lastblocktime' in s:
        state['lastblocktime'] = s['lastblocktime']

    elif 'txid' in s:
        state['tx'] = {
            'txid': s['txid'],
            'vin': [],
            'vout_string': [],
            'cursor': 0,
            'offset': 0,
            'out_offset': 0
        }

        for vin in s['vin']:
            if 'coinbase' in vin:
                state['tx']['vin'].append({'coinbase':  vin['coinbase']})
            elif 'txid' in vin:
                state['tx']['vin'].append({'txid': vin['txid'], 'vout': vin['vout']})

        for vout in s['vout']:
            if 'value' in vout:
                buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']
                state['tx']['vout_string'].extend(textwrap.wrap(buffer_string,73)) # change this to scale with window ?

        if state['mode'] == "transaction":
            tx.draw_window(state, window)

    return False
