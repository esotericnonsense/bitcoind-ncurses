#!/usr/bin/env python
import curses
import calendar
import gevent
import time

import global_mod as g
import getstr
import footer

class BlockViewer(object):
    def __init__(self, block_store, window):
        self._block_store = block_store
        self._window = window

        self._browse_height = None

    def draw(self):
        window.clear()
        window.refresh()
        win_header = curses.newwin(5, 75, 0, 0)

        if self._browse_height is not None:
            # TODO: try/except on KeyError here?
            blockhash = self._block_store.get_hash(browse_height)
            block = self._block_store.get_block(blockhash)

            win_header.addstr(0, 1, "height: " + str(block.blockheight).zfill(6) + "    (J/K: browse, HOME/END: quicker, L: latest, G: seek)", curses.A_BOLD)
            win_header.addstr(1, 1, "hash: " + block.blockhash, curses.A_BOLD)
            win_header.addstr(2, 1, "root: " + block.merkleroot, curses.A_BOLD)
            win_header.addstr(3, 1, "{} bytes ({} KB)".format(block.size, block.size/1024), curses.A_BOLD)
            win_header.addstr(3, 26, "diff: {:,d}".format(int(block.difficulty)), curses.A_BOLD)
            win_header.addstr(3, 52, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(block.time)), curses.A_BOLD)
            win_header.addstr(4, 51, ("v" + str(block.version)).rjust(20), curses.A_BOLD)

            # TODO: draw transactions (transaction store?)
            # draw_transactions(state)

        else:
            win_header.addstr(0, 1, "no block information loaded", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'G' to enter a block hash, height, or timestamp", curses.A_BOLD)

        win_header.refresh()
        footer.draw_window(state)
