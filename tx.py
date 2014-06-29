#!/usr/bin/env python
import curses, time

import global_mod as g
import getstr

def draw_window(state, window):
    # TODO: add transaction locktime, add sequence to inputs
    window.clear()
    window.refresh()
    win_header = curses.newwin(3, 75, 0, 0)

    if 'tx' in state:
        win_header.addstr(0, 1, "bitcoind-ncurses " + g.version + " [transaction mode] (press 'G' to enter a txid)", curses.color_pair(1) + curses.A_BOLD)
        win_header.addstr(1, 1, "txid: " + state['tx']['txid'], curses.A_BOLD)
        draw_inputs(state)
        draw_outputs(state)

    else:
        win_header.addstr(0, 1, "no transaction loaded", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'G' to enter a txid, or 'D' to return to main window", curses.A_BOLD)

    win_header.refresh()

def draw_inputs(state):
    win_inputs = curses.newwin(9, 75, 3, 0)
    win_inputs.addstr(0, 1, "inputs (UP/DOWN: select, SPACE: view)", curses.A_BOLD)

    offset = state['tx']['offset']

    for index in xrange(offset, offset+7):
        if index < len(state['tx']['vin']):
            if 'txid' in state['tx']['vin'][index]:
                if index == (state['tx']['cursor']):
                    win_inputs.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)
                win_inputs.addstr(index+1-offset, 3, state['tx']['vin'][index]['txid'] + ":" + "%03d" % state['tx']['vin'][index]['vout'])
            elif 'coinbase' in state['tx']['vin'][index]:
                win_inputs.addstr(index+1-offset, 3, "coinbase " + state['tx']['vin'][index]['coinbase'])

    if offset+7 < len(state['tx']['vin']):
        win_inputs.addstr(8, 3, "...")

    win_inputs.refresh()

def draw_outputs(state):
    win_outputs = curses.newwin(8, 75, 12, 0)
    if len(state['tx']['vout_string']) > 7:
        win_outputs.addstr(0, 1, "outputs (PGUP/PGDOWN: scroll)", curses.A_BOLD)
    else:
        win_outputs.addstr(0, 1, "outputs", curses.A_BOLD)

    offset = state['tx']['out_offset']

    for index in xrange(offset, offset+7):
        if index < len(state['tx']['vout_string']):
            win_outputs.addstr(index+1-offset, 1, state['tx']['vout_string'][index])
    win_outputs.refresh()

def draw_input_window(state, window, rpc_queue):
    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses " + g.version + " [transaction input mode]", curses.color_pair(1) + curses.A_BOLD)
    window.addstr(1, 1, "please enter txid", curses.A_BOLD)
    window.refresh()

    win_textbox = curses.newwin(1,67,3,1) # h,w,y,x
    entered_txid = getstr.getstr(win_textbox)

    if len(entered_txid) == 64: # TODO: better checking for valid txid here
        s = {'txid': entered_txid}
        rpc_queue.put(s)

        window.addstr(5, 1, "waiting for transaction (will stall here if not found)", curses.color_pair(1) + curses.A_BOLD)
        window.refresh()
        state['mode'] = "transaction"

    else:
        window.addstr(5, 1, "not a valid txid", curses.color_pair(1) + curses.A_BOLD)
        window.refresh()

        time.sleep(2)

        window.clear()
        window.refresh()
        state['mode'] = "monitor"
