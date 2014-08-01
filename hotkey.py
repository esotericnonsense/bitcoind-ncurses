#/usr/bin/env python
import curses

import global_mod as g
import tx
import block
import monitor
import peers
import wallet
import console
import net

def change_mode(state, window, mode):
    try:
        g.modes.index(mode)
    except ValueError:
        return False

    state['mode'] = mode

    if mode == 'monitor':
        monitor.draw_window(state, window)
    elif mode == 'transaction':
        tx.draw_window(state, window)
    elif mode == 'peers':
        peers.draw_window(state, window)
    elif mode == 'wallet':
        wallet.draw_window(state, window)
    elif mode == 'block':
        block.draw_window(state, window)
    elif mode == 'console':
        console.draw_window(state, window)
    elif mode == 'net':
        net.draw_window(state, window)

def key_left(state, window, rpc_queue):
    try:
        index = g.modes.index(state['mode']) - 1
    except:
        pass
    if index < 0:
        index = len(g.modes) - 2
    change_mode(state, window, g.modes[index])

def key_right(state, window, rpc_queue):
    try:
        index = g.modes.index(state['mode']) + 1
    except:
        pass
    if index > len(g.modes) - 2: # last index item is 'quit'
        index = 0
    change_mode(state, window, g.modes[index])

def key_w(state, window, rpc_queue):
    rpc_queue.put('listsinceblock')
    change_mode(state, window, 'wallet')

def key_p(state, window, rpc_queue):
    rpc_queue.put('getpeerinfo')
    change_mode(state, window, 'peers')

def key_g(state, window, rpc_queue):
    if state['mode'] == "transaction":
        state['mode'] = "transaction-input"
        tx.draw_input_window(state, window, rpc_queue)
    elif state['mode'] == "block":
        state['mode'] = "block-input"
        block.draw_input_window(state, window, rpc_queue)
    elif state['mode'] == "console":
        console.draw_input_box(state, rpc_queue)

def go_to_latest_block(state, window, rpc_queue):
    if state['mode'] == "block":
        if 'blockcount' in state:
            if state['blockcount'] not in state['blocks']:
                s = {'getblockhash': state['blockcount']}
                rpc_queue.put(s)
            else:
                state['blocks']['browse_height'] = state['blockcount']
                block.draw_window(state, window)

def scroll_down(state, window, rpc_queue):
    if state['mode'] == "transaction":
        if 'tx' in state:
            window_height = (state['y'] - 4) / 2
            if state['tx']['cursor'] < (len(state['tx']['vin']) - 1) and state['tx']['mode'] == 'inputs':
                state['tx']['cursor'] += 1

                if (state['tx']['cursor'] - state['tx']['offset']) > window_height-2:
                    state['tx']['offset'] += 1
                tx.draw_inputs(state)

            elif state['tx']['out_offset'] < (len(state['tx']['vout_string']) - (window_height-1)) and state['tx']['mode'] == 'outputs':
                state['tx']['out_offset'] += 1
                tx.draw_outputs(state)

    elif state['mode'] == "block":
        if 'blocks' in state:
            height = str(state['blocks']['browse_height'])
            if height in state['blocks']:
                blockdata = state['blocks'][height]
                if state['blocks']['cursor'] < (len(blockdata['tx']) - 1):
                    state['blocks']['cursor'] += 1
                    window_height = state['y'] - 6
                    if (state['blocks']['cursor'] - state['blocks']['offset']) > window_height-2:
                        state['blocks']['offset'] += 1
                    block.draw_transactions(state)

    elif state['mode'] == "peers":
        if 'peerinfo' in state and 'peerinfo_offset' in state:
            window_height = state['y'] - 4
            if state['peerinfo_offset'] < (len(state['peerinfo']) - window_height):
                state['peerinfo_offset'] += 1
                peers.draw_peers(state)

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            if state['wallet']['cursor'] < (len(state['wallet']['transactions']) - 1):
                state['wallet']['cursor'] += 1
                window_height = state['y'] - 3
                if ( (state['wallet']['cursor']*4 +1 ) - state['wallet']['offset']) > window_height-2:
                    state['wallet']['offset'] += 4
                wallet.draw_transactions(state)

    elif state['mode'] == "console":
        if state['console']['offset'] > 0:
            state['console']['offset'] -= 1
            console.draw_buffer(state)

def scroll_up(state, window, rpc_queue):
    if state['mode'] == "transaction":
        if 'tx' in state:
            if state['tx']['cursor'] > 0 and state['tx']['mode'] == 'inputs':
                if (state['tx']['cursor'] - state['tx']['offset']) == 0:
                    state['tx']['offset'] -= 1
                state['tx']['cursor'] -= 1
                tx.draw_inputs(state)

            if state['tx']['out_offset'] > 0 and state['tx']['mode'] == 'outputs':
                state['tx']['out_offset'] -= 1
                tx.draw_outputs(state)

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
            if state['wallet']['cursor'] > 0:
                state['wallet']['cursor'] -= 1
                if ((state['wallet']['cursor']*4 +1) - state['wallet']['offset']) == -3:
                    state['wallet']['offset'] -= 4
                wallet.draw_transactions(state)

    elif state['mode'] == "console":
        state['console']['offset'] += 1
        console.draw_buffer(state)

def scroll_up_page(state, window, rpc_queue):
    if state['mode'] == "console":
        window_height = state['y'] - 3 - 2
        state['console']['offset'] += window_height
        console.draw_buffer(state)

def scroll_down_page(state, window, rpc_queue):
    if state['mode'] == "console":
        window_height = state['y'] - 3 - 2
        if state['console']['offset'] > window_height:
            state['console']['offset'] -= window_height
        else:
            state['console']['offset'] = 0
        console.draw_buffer(state)

def toggle_inputs_outputs(state, window, rpc_queue):
    if state['mode'] == "transaction":
        if 'tx' in state:
            if 'mode' in state['tx']:
                if state['tx']['mode'] == 'inputs':
                    state['tx']['mode'] = 'outputs'
                else:
                    state['tx']['mode'] = 'inputs'
                tx.draw_window(state, window)

def load_transaction(state, window, rpc_queue):
    # TODO: some sort of indicator that a transaction is loading
    if state['mode'] == "transaction":
        if 'tx' in state:
            if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]:
                if state['tx']['loaded']:
                    state['tx']['loaded'] = 0
                    s = {'txid': state['tx']['vin'][ state['tx']['cursor'] ]['txid']}
                    rpc_queue.put(s)

    elif state['mode'] == "block":
        if 'blocks' in state:
            if state['blocks']['browse_height'] > 0: # block 0 is not indexed
                height = str(state['blocks']['browse_height'])
                if height in state['blocks']:
                    blockdata = state['blocks'][height]
                    s = {'txid': blockdata['tx'][ state['blocks']['cursor'] ]}
                    rpc_queue.put(s)
                    state['mode'] = "transaction"

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            if 'transactions' in state['wallet']:
                s = {'txid': state['wallet']['transactions'][ state['wallet']['cursor'] ]['txid']}
                rpc_queue.put(s)
                state['mode'] = "transaction"

def toggle_verbose_mode(state, window, rpc_queue):
    if state['mode'] == "transaction":
        if 'tx' in state:
            if 'txid' in state['tx']:
                if state['tx']['loaded']:
                    state['tx']['loaded'] = 0

                    if 'total_inputs' not in state['tx']:
                        s = {'txid': state['tx']['txid'], 'verbose': 1}
                    else:
                        s = {'txid': state['tx']['txid']}

                    rpc_queue.put(s)

def block_seek_back_one(state, window, rpc_queue):
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

def block_seek_forward_one(state, window, rpc_queue):
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

def block_seek_back_thousand(state, window, rpc_queue):
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

def block_seek_forward_thousand(state, window, rpc_queue):
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

keymap = {
    curses.KEY_LEFT: key_left,
    curses.KEY_RIGHT: key_right,
    curses.KEY_DOWN: scroll_down,
    curses.KEY_UP: scroll_up,
    curses.KEY_PPAGE: scroll_up_page,
    curses.KEY_NPAGE: scroll_down_page,
    curses.KEY_HOME: block_seek_back_thousand,
    curses.KEY_END: block_seek_forward_thousand,

    curses.KEY_ENTER: load_transaction,
    ord('\n'): load_transaction,

    ord('w'): key_w,
    ord('W'): key_w,

    ord('p'): key_p,
    ord('P'): key_p,

    ord('g'): key_g,
    ord('G'): key_g,

    ord('l'): go_to_latest_block,
    ord('L'): go_to_latest_block,

    ord('\t'): toggle_inputs_outputs,
    9: toggle_inputs_outputs,

    ord("v"): toggle_verbose_mode,
    ord("V"): toggle_verbose_mode,

    ord('j'): block_seek_back_one,
    ord('J'): block_seek_back_one,

    ord('k'): block_seek_forward_one,
    ord('K'): block_seek_forward_one
}

def check(state, window, rpc_queue):
    key = window.getch()

    if key < 0:
        pass

    elif key in keymap:
        keymap[key](state, window, rpc_queue)

    elif key == ord('q') or key == ord('Q'): # quit
        return True

    elif key == ord('m') or key == ord('M'):
        change_mode(state, window, 'monitor')

    elif key == ord('b') or key == ord('B'):
        change_mode(state, window, 'block')

    elif key == ord('t') or key == ord('T'):
        change_mode(state, window, 'transaction')

    elif key == ord('c') or key == ord('C'):
        change_mode(state, window, 'console')

    elif key == ord('n') or key == ord('N'):
        change_mode(state, window, 'net')

    return False

