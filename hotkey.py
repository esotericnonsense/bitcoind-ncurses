#/usr/bin/env python
import curses

import global_mod as g
import tx
import monitor
import peers
import wallet
import console
import net
import forks
import footer

def change_mode(block_viewer, state, window, mode, poller):
    try:
        g.modes.index(mode)
    except ValueError:
        return False

    state['mode'] = mode
    block_viewer._mode = mode

    if mode == 'monitor':
        monitor.draw_window(state, window)
    elif mode == 'tx':
        tx.draw_window(state, window)
    elif mode == 'peers':
        peers.draw_window(state, window)
    elif mode == 'wallet':
        wallet.draw_window(state, window)
    elif mode == 'block':
        block_viewer.draw()
    elif mode == 'console':
        console.draw_window(state, window)
    elif mode == 'net':
        net.draw_window(state, window)
    elif mode == 'forks':
        forks.draw_window(state, window)

    footer.draw_window(state)
    poller.set_mode(mode)

def key_left(state, window, rpcc, poller):
    try:
        index = g.modes.index(state['mode']) - 1
        if index < 0:
            index = len(g.modes) - 2
        change_mode(state, window, g.modes[index], poller)
    except:
        pass

def key_right(state, window, rpcc, poller):
    try:
        index = g.modes.index(state['mode']) + 1
        if index > len(g.modes) - 2: # last index item is 'quit'
            index = 0
        change_mode(state, window, g.modes[index], poller)
    except:
        pass

def key_g(state, window, rpcc, poller):
    if state['mode'] == 'tx':
        state['mode'] = "transaction-input"
        tx.draw_input_window(state, window, rpcc)
    elif state['mode'] == "block":
        state['mode'] = "block-input"
        block.draw_input_window(state, window, rpcc)
    elif state['mode'] == "console":
        console.draw_input_box(state, window, rpcc)

def go_to_latest_block(state, window, rpcc, poller):
    if state['mode'] == "block":
        if 'mininginfo' in state:
            if str(state['mininginfo']['blocks']) not in state['blocks']:
                rpcc.request("getblockhash", state["mininginfo"]["blocks"])
            else:
                state['blocks']['browse_height'] = state['mininginfo']['blocks']
                block.draw_window(state, window)

def scroll_down(state, window, rpcc, poller):
    if state['mode'] == 'tx':
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

    elif state['mode'] == "forks":
        if 'chaintips' in state and 'chaintips_offset' in state:
            window_height = state['y'] - 4
            if state['chaintips_offset'] < (len(state['chaintips']) - window_height):
                state['chaintips_offset'] += 1
                forks.draw_tips(state)

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

def scroll_up(state, window, rpcc, poller):
    if state['mode'] == 'tx':
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

    elif state['mode'] == "forks":
        if 'chaintips' in state and 'chaintips_offset' in state:
            if state['chaintips_offset'] > 0:
                state['chaintips_offset'] -= 1
                forks.draw_tips(state)

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

def scroll_up_page(state, window, rpcc, poller):
    if state['mode'] == "console":
        window_height = state['y'] - 3 - 2
        state['console']['offset'] += window_height
        console.draw_buffer(state)

def scroll_down_page(state, window, rpcc, poller):
    if state['mode'] == "console":
        window_height = state['y'] - 3 - 2
        if state['console']['offset'] > window_height:
            state['console']['offset'] -= window_height
        else:
            state['console']['offset'] = 0
        console.draw_buffer(state)

def toggle_inputs_outputs(state, window, rpcc, poller):
    if state['mode'] == 'tx':
        if 'tx' in state:
            if 'mode' in state['tx']:
                if state['tx']['mode'] == 'inputs':
                    state['tx']['mode'] = 'outputs'
                else:
                    state['tx']['mode'] = 'inputs'
                tx.draw_window(state, window)

def load_transaction(state, window, rpcc, poller):
    # TODO: some sort of indicator that a transaction is loading
    if state['mode'] == 'tx':
        if 'tx' in state:
            if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]:
                if state['tx']['loaded']:
                    state['tx']['loaded'] = 0
                    rpcc.request("getrawtransaction", state["tx"]["vin"][state["tx"]["cursor"]]["txid"], 1)

    elif state['mode'] == "block":
        if 'blocks' in state:
            if state['blocks']['browse_height'] > 0: # block 0 is not indexed
                height = str(state['blocks']['browse_height'])
                if height in state['blocks']:
                    blockdata = state['blocks'][height]
                    rpcc.request("getrawtransaction", blockdata["tx"][state["blocks"]["cursor"]], 1)
                    change_mode(state, window, "tx", poller)

    elif state['mode'] == "wallet":
        if 'wallet' in state:
            if 'transactions' in state['wallet']:
                rpcc.request("getrawtransaction", state['wallet']['transactions'][ state['wallet']['cursor'] ]['txid'], 1)
                change_mode(state, window, "tx", poller)

def toggle_verbose_mode(state, window, rpcc, poller):
    # TODO: Re-implement verbose mode
    return

    if state['mode'] == 'tx':
        if 'tx' in state:
            if 'txid' in state['tx']:
                if state['tx']['loaded']:
                    state['tx']['loaded'] = 0

                    if 'total_inputs' not in state['tx']:
                        s = {'txid': state['tx']['txid'], 'verbose': 1}
                    else:
                        s = {'txid': state['tx']['txid']}

                    rpcc.request(s)

def block_seek_back_one(state, window, rpcc, poller):
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
                        rpcc.request("getblockhash", state["blocks"]["browse_height"])

def block_seek_forward_one(state, window, rpcc, poller):
    if state['mode'] == "block":
        if 'blocks' in state:
            if state['blocks']['browse_height'] < state['mininginfo']['blocks']:
                if state['blocks']['loaded'] == 1:
                    state['blocks']['loaded'] = 0
                    state['blocks']['browse_height'] += 1
                    state['blocks']['cursor'] = 0
                    state['blocks']['offset'] = 0
                    if str(state['blocks']['browse_height']) in state['blocks']:
                        block.draw_window(state, window)
                    else:
                        rpcc.request("getblockhash", state["blocks"]["browse_height"])

def block_seek_back_thousand(state, window, rpcc, poller):
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
                        rpcc.request("getblockhash", state["blocks"]["browse_height"])

def block_seek_forward_thousand(state, window, rpcc, poller):
    if state['mode'] == "block":
        if 'blocks' in state:
            if (state['blocks']['browse_height']) < state['mininginfo']['blocks'] - 999:
                if state['blocks']['loaded'] == 1:
                    state['blocks']['loaded'] = 0
                    state['blocks']['browse_height'] += 1000
                    state['blocks']['cursor'] = 0
                    state['blocks']['offset'] = 0
                    if str(state['blocks']['browse_height']) in state['blocks']:
                        block.draw_window(state, window)
                    else:
                        rpcc.request("getblockhash", state["blocks"]["browse_height"])

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

modemap = {
    ord('m'): 'monitor',
    ord('M'): 'monitor',

    ord('b'): 'block',
    ord('B'): 'block',

    ord('t'): 'tx',
    ord('T'): 'tx',

    ord('c'): 'console',
    ord('C'): 'console',

    ord('n'): 'net',
    ord('N'): 'net',

    ord('p'): 'peers',
    ord('P'): 'peers',

    ord('w'): 'wallet',
    ord('W'): 'wallet',

    ord('f'): 'forks',
    ord('F'): 'forks',
}

def check(block_viewer, state, window, rpcc, poller):
    key = window.getch()

    if key < 0 or state['mode'] == 'splash':
        pass

    elif key in keymap:
        keymap[key](state, window, rpcc, poller)

    elif key in modemap:
        mode = modemap[key]

        if mode == "forks":
            rpcc.request('getchaintips')

        change_mode(block_viewer, state, window, mode, poller)

    elif key == ord('q') or key == ord('Q'): # quit
        return True

    return False
