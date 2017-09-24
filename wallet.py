#!/usr/bin/env python
import curses

import global_mod as g

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(2, 76, 0, 0)

    unit = 'BTC'
    if 'testnet' in state:
        if state['testnet']:
            unit = 'TNC'

    if 'wallet' in state:
        if 'balance' in state:
            balance_string = "balance: " + "%0.8f" % state['balance'] + " " + unit
            if 'unconfirmedbalance' in state:
                if state['unconfirmedbalance'] != 0:
                    balance_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
            window.addstr(0, 1, balance_string, curses.A_BOLD)

        draw_transactions(state)

    else:
        win_header.addstr(0, 1, "no wallet information loaded", curses.A_BOLD + curses.color_pair(3))
        win_header.addstr(1, 1, "loading... (is -disablewallet on?)", curses.A_BOLD)

    win_header.refresh()

def draw_transactions(state):
    window_height = state['y'] - 3
    win_transactions = curses.newwin(window_height, 76, 2, 0)

    win_transactions.addstr(0, 1, "transactions:                               (UP/DOWN: scroll, ENTER: view)", curses.A_BOLD + curses.color_pair(5))

    offset = state['wallet']['offset']

    for index in range(offset, offset+window_height-1):
        if index < len(state['wallet']['view_string']):
                condition = (index == offset+window_height-2) and (index+1 < len(state['wallet']['view_string']))
                condition = condition or ( (index == offset) and (index > 0) )

                if condition:
                    win_transactions.addstr(index+1-offset, 1, "...")
                else:
                    win_transactions.addstr(index+1-offset, 1, state['wallet']['view_string'][index])

                if index == (state['wallet']['cursor']*4 + 1):
                    win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

    win_transactions.refresh()
