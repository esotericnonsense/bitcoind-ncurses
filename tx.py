#!/usr/bin/env python
import curses, time

import global_mod as g
import getstr

def draw_window(state, window):
    # TODO: add transaction locktime, add sequence to inputs
    window.clear()
    window.refresh()
    win_header = curses.newwin(4, 75, 0, 0)

    if 'tx' in state:
        color = curses.color_pair(1)
        if 'testnet' in state:
            if state['testnet']: color = curses.color_pair(2)
        win_header.addstr(0, 1, "bitcoind-ncurses " + g.version + " [transaction mode] (press 'G' to enter a txid)", color + curses.A_BOLD)
        win_header.addstr(1, 1, "txid: " + state['tx']['txid'], curses.A_BOLD)
        win_header.addstr(2, 1, str(state['tx']['size']) + " bytes (" + str(state['tx']['size']/1024) + " KB)       ", curses.A_BOLD)

        if 'total_outputs' in state['tx']:
            output_string = "%.8f" % state['tx']['total_outputs'] + " BTC"
            if 'total_inputs' in state['tx']:
                fee = state['tx']['total_inputs'] - state['tx']['total_outputs']
                output_string += " + " + "%.8f" % fee + " BTC fee"
            else:
                output_string += " + ??? BTC fee"
            win_header.addstr(2, 26, output_string.rjust(45), curses.A_BOLD)

        if 'confirmations' in state['tx']:
            win_header.addstr(3, 1, str(state['tx']['confirmations']) + " conf", curses.A_BOLD)
        else:
            win_header.addstr(3, 1, "unconfirmed", curses.A_BOLD)


        draw_inputs(state)
        draw_outputs(state)

    else:
        win_header.addstr(0, 1, "no transaction loaded", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'G' to enter a txid", curses.A_BOLD)
        win_header.addstr(2, 1, "or 'M' to return to monitor window", curses.A_BOLD)

    win_header.refresh()

def draw_inputs(state):
    window_height = (state['y'] - 4) / 2
    window_width = state['x']
    win_inputs = curses.newwin(window_height, window_width+1, 4, 0)
    win_inputs.addstr(0, 1, "inputs:                     (UP/DOWN: select, SPACE: view, V: verbose)", curses.A_BOLD + curses.color_pair(5))

    # reset cursor if it's been resized off the bottom
    if state['tx']['cursor'] > state['tx']['offset'] + (window_height-2):
        state['tx']['offset'] = state['tx']['cursor'] - (window_height-2)

    offset = state['tx']['offset']

    for index in xrange(offset, offset+window_height-1):
        if index < len(state['tx']['vin']):
            if 'txid' in state['tx']['vin'][index]:

                buffer_string = state['tx']['vin'][index]['txid'] + ":" + "%03d" % state['tx']['vin'][index]['vout']
                if 'prev_tx' in state['tx']['vin'][index]:
                    vout = state['tx']['vin'][index]['prev_tx']

                    if 'value' in vout:
                        if vout['scriptPubKey']['type'] == "pubkeyhash":
                            buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['addresses'][0].ljust(34)
                        else:
                            if len(vout['scriptPubKey']['asm']) > window_width-37:
                                buffer_string = "% 14.8f" % vout['value'] + ": ..." + vout['scriptPubKey']['asm'][-(window_width-40):]
                            else:
                                buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']

                        length = len(buffer_string)
                        if length + 71 < window_width:
                            buffer_string += " " + state['tx']['vin'][index]['txid'] + ":" + "%03d" % state['tx']['vin'][index]['vout']
                        else:
                            buffer_string += " " + state['tx']['vin'][index]['txid'][:(window_width-length-13)] + "[...]:" + "%03d" % state['tx']['vin'][index]['vout']

                if index == (state['tx']['cursor']):
                    win_inputs.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

                if (index == offset+window_height-2) and (index+1 < len(state['tx']['vin'])):
                    win_inputs.addstr(index+1-offset, 3, "... ")
                elif (index == offset) and (index > 0):
                    win_inputs.addstr(index+1-offset, 3, "... ")
                else:
                    win_inputs.addstr(index+1-offset, 3, buffer_string)

            elif 'coinbase' in state['tx']['vin'][index]:
                win_inputs.addstr(index+1-offset, 3, "coinbase " + state['tx']['vin'][index]['coinbase'])

    win_inputs.refresh()

def draw_outputs(state):
    window_height = (state['y'] - 4) / 2
    win_outputs = curses.newwin(window_height, 75, 4+window_height, 0)
    if len(state['tx']['vout_string']) > window_height-1:
        win_outputs.addstr(0, 1, "outputs:                                         (PGUP/PGDOWN: scroll)", curses.A_BOLD + curses.color_pair(5))
    else:
        win_outputs.addstr(0, 1, "outputs:", curses.A_BOLD + curses.color_pair(5))

    offset = state['tx']['out_offset']

    for index in xrange(offset, offset+window_height-1):
        if index < len(state['tx']['vout_string']):
            if (index == offset+window_height-2) and (index+1 < len(state['tx']['vout_string'])):
                win_outputs.addstr(index+1-offset, 1, "... ")
            elif (index == offset) and (index > 0):
                win_outputs.addstr(index+1-offset, 1, "... ")
            else:
                win_outputs.addstr(index+1-offset, 1, state['tx']['vout_string'][index])
    win_outputs.refresh()

def draw_input_window(state, window, rpc_queue):
    color = curses.color_pair(1)
    if 'testnet' in state:
        if state['testnet']: color = curses.color_pair(2)

    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses " + g.version + " [transaction input mode]", color + curses.A_BOLD)
    window.addstr(1, 1, "please enter txid", curses.A_BOLD)
    window.refresh()

    entered_txid = getstr.getstr(67, 3, 1) # w, y, x

    if len(entered_txid) == 64: # TODO: better checking for valid txid here
        s = {'txid': entered_txid}
        rpc_queue.put(s)

        window.addstr(5, 1, "waiting for transaction (will stall here if not found)", color + curses.A_BOLD)
        window.refresh()
        state['mode'] = "transaction"

    else:
        window.addstr(5, 1, "not a valid txid", color + curses.A_BOLD)
        window.refresh()

        time.sleep(0.5)

        window.clear()
        window.refresh()
        state['mode'] = "monitor"
