#!/usr/bin/env python
import curses, time

import global_mod as g

def draw_window(state, window):
    # TODO: only draw parts that actually changed
    window.clear()

    if 'version' in state:
        if state['testnet'] == 1:
            window.addstr(0, 1, "bitcoind-ncurses " + g.version, curses.color_pair(2) + curses.A_BOLD)
            window.addstr(1, 1, "bitcoind v" + state['version'] + " (testnet)", curses.color_pair(2) + curses.A_BOLD)
        else:
            window.addstr(0, 1, "bitcoind-ncurses " + g.version, curses.color_pair(1) + curses.A_BOLD)
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
            window.addstr(5, 1, "Transactions:" + "% 4d" % len(blockdata['tx']))

            window.addstr(4, 38, "Timestamp: " + time.asctime(time.gmtime(blockdata['time'])))

            if state['lastblocktime'] == 0:
                recvdelta_string = "       "
            else:
                recvdelta = int(time.time() - state['lastblocktime'])
                m, s = divmod(recvdelta, 60)
                h, m = divmod(m, 60)
                recvdelta_string = "{:01d}:{:02d}:{:02d}".format(h,m,s)

            stampdelta = int(time.time() - blockdata['time'])
            if stampdelta > 3600*3: # probably syncing if it's three hours old
                stampdelta_string = "             (syncing)"
            elif stampdelta > 0:
                m, s = divmod(stampdelta, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                stampdelta_string = "({:d}d {:02d}:{:02d}:{:02d} by stamp)".format(d,h,m,s)
            else:
                stampdelta_string = "     (stamp in future)"

            window.addstr(5, 38, "Age: " + recvdelta_string + " " + stampdelta_string)

    if 'difficulty' in state:
        diff = int(state['difficulty'])
        window.addstr(7, 1, "Diff:  " + "{:,d}".format(diff))

    index = 7
    for block_avg in state['networkhashps']:
        rate = state['networkhashps'][block_avg]
        if block_avg == 2016:
            nextdiff = (rate*600)/(2**32)
            window.addstr(8, 1, "Next: ~" + "{:,d}".format(nextdiff))
        if rate > 10**18:
            rate /= 10**18
            suffix = " EH/s"
        elif rate > 10**12:
            rate /= 10**12
            suffix = " TH/s"
        else:
            rate /= 10**6
            suffix = " MH/s"
        rate_string = "{:,d}".format(rate) + suffix
        window.addstr(index, 38, "Hashrate (" + str(block_avg).rjust(4) + "): " + rate_string)
        index += 1

    if 'totalbytesrecv' in state:
        window.addstr(0, 57, "D: " + "% 10.2f" % (state['totalbytesrecv']*1.0/1048576) + " MB", curses.A_BOLD)
        window.addstr(1, 57, "U: " + "% 10.2f" % (state['totalbytessent']*1.0/1048576) + " MB", curses.A_BOLD)

    window.addstr(18, 1, "Hotkeys: T (transaction viewer), B (block viewer), M (this screen)", curses.A_BOLD)
    window.addstr(19, 1, "         Q (exit bitcoind-ncurses)", curses.A_BOLD)

    window.refresh()
