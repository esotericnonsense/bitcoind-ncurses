#/usr/bin/env python
import curses

import tx
import block
import monitor
import peers
import wallet

def check(state, window, rpc_queue):
    c = window.getch()

    if not c:
        return False

    elif c == ord('q') or c == ord('Q'):
        return True

    elif c == ord('m') or c == ord('M'):
        state['mode'] = "monitor"
        monitor.draw_window(state, window)

    elif c == ord('t') or c == ord('T'):
        state['mode'] = "transaction"
        tx.draw_window(state, window)

    elif c == ord('p') or c == ord('P'):
        rpc_queue.put('getpeerinfo')
        state['mode'] = "peers"

    elif c == ord('w') or c == ord('W'):
        rpc_queue.put('listsinceblock')
        state['mode'] = "wallet"

    elif c == ord('g') or c == ord('G'):
        if state['mode'] == "transaction":
            state['mode'] = "transaction-input"
            tx.draw_input_window(state, window, rpc_queue)
        elif state['mode'] == "block":
            state['mode'] = "block-input"
            block.draw_input_window(state, window, rpc_queue)

    elif c == ord('b') or c == ord('B'):
        state['mode'] = "block"
        block.draw_window(state, window)

    elif c == ord('l') or c == ord('L'):
        if state['mode'] == "block":
            if 'blockcount' in state:
                if state['blockcount'] not in state['blocks']:
                    s = {'getblockhash': state['blockcount']}
                    rpc_queue.put(s)
                else:
                    state['blocks']['browse_height'] = state['blockcount']
                    block.draw_window(state, window)

    elif c == curses.KEY_DOWN:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] < (len(state['tx']['vin']) - 1):
                    state['tx']['cursor'] += 1

                    window_height = (state['y'] - 4) / 2

                    if (state['tx']['cursor'] - state['tx']['offset']) > window_height-2:
                        state['tx']['offset'] += 1
                    tx.draw_inputs(state)

        elif state['mode'] == "block":
            if 'blocks' in state:
                height = str(state['blocks']['browse_height'])
                if height in state['blocks']:
                    blockdata = state['blocks'][height]
                    if state['blocks']['cursor'] < (len(blockdata['tx']) - 1):
                        state['blocks']['cursor'] += 1
                        if (state['blocks']['cursor'] - state['blocks']['offset']) > 14:
                            state['blocks']['offset'] += 1
                        block.draw_transactions(state)

        elif state['mode'] == "peers":
            if 'peerinfo' in state and 'peerinfo_offset' in state:
                if state['peerinfo_offset'] < (len(state['peerinfo']) - 17):
                    state['peerinfo_offset'] += 1
                    peers.draw_peers(state)

        elif state['mode'] == "wallet":
            if 'wallet' in state: 
                if state['wallet']['offset'] < (len(state['wallet']['view_string']) - 16):
                    state['wallet']['offset'] += 4
                    wallet.draw_transactions(state)

    elif c == curses.KEY_UP:
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

        elif state['mode'] == "peers":
            if 'peerinfo' in state and 'peerinfo_offset' in state:
                if state['peerinfo_offset'] > 0:
                    state['peerinfo_offset'] -= 1
                    peers.draw_peers(state)

        elif state['mode'] == "wallet":
            if 'wallet' in state:
                if state['wallet']['offset'] > 0:
                    state['wallet']['offset'] -= 4
                    wallet.draw_transactions(state)

    elif c == curses.KEY_PPAGE:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['out_offset'] > 1:
                    state['tx']['out_offset'] -= 2
                    tx.draw_outputs(state)

    elif c == curses.KEY_NPAGE:
        if state['mode'] == "transaction":
            if 'tx' in state:
                window_height = (state['y'] - 4) / 2
                if state['tx']['out_offset'] < (len(state['tx']['vout_string']) - (window_height-1)):
                    state['tx']['out_offset'] += 2
                    tx.draw_outputs(state)

    elif c == ord(' '):
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

    elif c == ord("v") or c == ord("V"):
        if state['mode'] == "transaction":
            if 'tx' in state:
                if 'txid' in state['tx']:
                    s = {'txid': state['tx']['txid'], 'verbose': 1}
                    rpc_queue.put(s)

    elif c == curses.KEY_LEFT:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) > 0:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] -= 1
                        state['blocks']['cursor'] = 0
                        state['blocks']['offset'] = 0
                        if str(state['blocks']['browse_height']) in state['blocks']:
                            block.draw_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    elif c == curses.KEY_RIGHT:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) < state['blockcount']:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] += 1
                        state['blocks']['cursor'] = 0
                        state['blocks']['offset'] = 0
                        if str(state['blocks']['browse_height']) in state['blocks']:
                            block.draw_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    elif c == curses.KEY_HOME:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) > 999:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] -= 1000
                        state['blocks']['cursor'] = 0
                        state['blocks']['offset'] = 0
                        if str(state['blocks']['browse_height']) in state['blocks']:
                            block.draw_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    elif c == curses.KEY_END:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) < state['blockcount'] - 999:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] += 1000
                        state['blocks']['cursor'] = 0
                        state['blocks']['offset'] = 0
                        if str(state['blocks']['browse_height']) in state['blocks']:
                            block.draw_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    return False
