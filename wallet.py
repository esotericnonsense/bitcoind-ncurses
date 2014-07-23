#!/usr/bin/env python
import curses

import global_mod as g

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(3, 75, 0, 0)

    if 'wallet' in state:
        color = curses.color_pair(1)
        if 'testnet' in state:
            if state['testnet']: color = curses.color_pair(2)
        win_header.addstr(0, 1, "bitcoind-ncurses " + g.version + "        [wallet mode]       (press 'W' to refresh)", color + curses.A_BOLD)

        if 'balance' in state:
            balance_string = "balance: " + "%0.8f" % state['balance'] + " BTC"
            if 'unconfirmedbalance' in state:
                if state['unconfirmedbalance'] != 0:
                    balance_string += " (+" + "%0.8f" % state['unconfirmedbalance'] + " unconf)"
            window.addstr(1, 1, balance_string, curses.A_BOLD)
        draw_transactions(state)

    else:
        win_header.addstr(0, 1, "wallet transactions not loaded - is disablewallet enabled?", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'W' to refresh", curses.A_BOLD)
        win_header.addstr(2, 1, "or 'M' to return to monitor window", curses.A_BOLD)

    win_header.refresh()

def draw_transactions(state):
    window_height = state['y'] - 3
    win_transactions = curses.newwin(window_height, 76, 3, 0)
    if len(state['wallet']['view_string']) > window_height-1:
        win_transactions.addstr(0, 1, "transactions:                                            (UP/DOWN: scroll)", curses.A_BOLD + curses.color_pair(5))
    else:
        win_transactions.addstr(0, 1, "transactions:", curses.A_BOLD + curses.color_pair(5))

    offset = state['wallet']['offset']

    for index in xrange(offset, offset+window_height-1):
        if index < len(state['wallet']['view_string']):
                win_transactions.addstr(index+1-offset, 1, state['wallet']['view_string'][index])
                if (index == offset+window_height-2) and (index+1 < len(state['wallet']['view_string'])):
                    win_transactions.addstr(index+1-offset, 1, "...                                                                       ")
                elif (index == offset) and (index > 0):
                    win_transactions.addstr(index+1-offset, 1, "...                ")
    win_transactions.refresh()
