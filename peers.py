#!/usr/bin/env python
import curses

import global_mod as g

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(2, 75, 0, 0)

    if 'peerinfo' in state:
        color = curses.color_pair(1)
        if 'testnet' in state:
            if state['testnet']: color = curses.color_pair(2)
        win_header.addstr(0, 1, "bitcoind-ncurses " + g.version + " [peer view] (press 'P' to refresh)", color + curses.A_BOLD)
        draw_peers(state)

    else:
        win_header.addstr(0, 1, "peer info not loaded (this should not happen!)", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'M' to return to main window", curses.A_BOLD)

    win_header.refresh()

def draw_peers(state):
    win_peers = curses.newwin(18, 75, 2, 0)
    win_peers.addstr(0, 1, "Peers: " + "% 4d" % len(state['peerinfo']) + " (scrolling not yet implemented)              Recv        Sent", curses.A_BOLD)

    for index in xrange(0, 17):
        if index < len(state['peerinfo']):
            peer = state['peerinfo'][index]
            if peer['inbound']:
                win_peers.addstr(index+1, 1, 'I')
            win_peers.addstr(index+1, 3, peer['addr'])
            win_peers.addstr(index+1, 32, peer['subver'].strip("/"))
            win_peers.addstr(index+1, 50, str(peer['bytesrecv'] / 1024).rjust(10) + 'KB')
            win_peers.addstr(index+1, 62, str(peer['bytessent'] / 1024).rjust(10) + 'KB')

    win_peers.refresh()
