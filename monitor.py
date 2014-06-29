#!/usr/bin/env python
import curses, time

import global_mod as g

def draw_window(state, window):
    # TODO: only draw parts that actually changed
    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses " + g.version, curses.color_pair(1) + curses.A_BOLD)

    if 'version' in state:
        if state['testnet'] == 1:
            window.addstr(1, 1, "bitcoind v" + state['version'] + " (testnet)", curses.color_pair(2) + curses.A_BOLD)
        else:
            window.addstr(1, 1, "bitcoind v" + state['version'] + " ", curses.color_pair(1) + curses.A_BOLD)

    if 'peers' in state:
        window.addstr(0, 32, str(state['peers']) + " peers    ", curses.A_BOLD)

    if 'balance' in state:
        window.addstr(1, 32, "%0.8f" % state['balance'] + " BTC", curses.A_BOLD)

    if 'blockcount' in state:
        height = str(state['blockcount'])
        if height in state['blocks']:
            blockdata = state['blocks'][str(height)]

            window.addstr(3, 1, height.zfill(6) + ": " + str(blockdata['hash']))
            window.addstr(4, 1, str(blockdata['size']) + " bytes (" + str(blockdata['size']/1024) + " KB)       ")
            window.addstr(4, 38, "Timestamp: " + time.asctime(time.gmtime(blockdata['time'])))

            lastblockmins = int((time.time() - state['lastblocktime']) / 60)
            lastblocksecs = int((time.time() - state['lastblocktime']) % 60)

            if (lastblockmins > 0): window.addstr(6, 38, "Received " + str(lastblockmins) + "m " + str(lastblocksecs) + "s ago      ")
            else: window.addstr(6, 38, "Received " + str(lastblocksecs) + "s ago           ")

            since_last_block_timestamp = time.time() - blockdata['time']
            if (since_last_block_timestamp > 3600*3):    # assume over 3 hours is syncing
                window.addstr(6, 64, "(syncing)", curses.color_pair(3))

            window.addstr(5, 38, "Now (UTC): " + time.asctime(time.gmtime(time.time())))

    if 'totalbytesrecv' in state:
        window.addstr(0, 57, "D: " + "% 10.2f" % (state['totalbytesrecv']*1.0/1048576) + " MB", curses.A_BOLD)
        window.addstr(1, 57, "U: " + "% 10.2f" % (state['totalbytessent']*1.0/1048576) + " MB", curses.A_BOLD)

    window.addstr(8, 1, "Hotkeys: T (transaction viewer), B (block viewer), D (this screen)", curses.A_BOLD)
    window.addstr(9, 1, "         Q (exit bitcoind-ncurses), G (manually enter txid)", curses.A_BOLD)

    window.refresh()
