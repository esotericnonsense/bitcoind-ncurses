#!/usr/bin/env python
import curses
import calendar
import gevent
import time

import global_mod as g
import getstr

class BlockViewer(object):
    def __init__(self, block_store, window):
        self._block_store = block_store
        self._window = window

        self._mode = None # TODO debug

        self._browse_height = None

    def on_block(self, block):
        if not self._browse_height:
            self._browse_height = block.blockheight

        if self._mode and self._mode == "block":
            self.draw()

    def draw(self):
        def draw_block(block):
            win_header = curses.newwin(5, 75, 0, 0)
            win_header.addstr(0, 1, "height: " + str(block.blockheight).zfill(6) + "    (J/K: browse, HOME/END: quicker, L: latest, G: seek)", curses.A_BOLD)
            win_header.addstr(1, 1, "hash: " + block.blockhash, curses.A_BOLD)
            win_header.addstr(2, 1, "root: " + block.merkleroot, curses.A_BOLD)
            win_header.addstr(3, 1, "{} bytes ({} KB)".format(block.size, block.size/1024), curses.A_BOLD)
            win_header.addstr(3, 26, "diff: {:,d}".format(int(block.difficulty)), curses.A_BOLD)
            win_header.addstr(3, 52, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(block.time)), curses.A_BOLD)
            win_header.addstr(4, 51, ("v" + str(block.version)).rjust(20), curses.A_BOLD)
            win_header.refresh()

        def draw_no_block():
            win_header = curses.newwin(5, 75, 0, 0)
            win_header.addstr(0, 1, "no block information loaded", curses.A_BOLD + curses.color_pair(3))
            win_header.addstr(1, 1, "press 'G' to enter a block hash, height, or timestamp", curses.A_BOLD)
            win_header.refresh()

        self._window.clear()
        self._window.refresh()

        if self._browse_height is not None:
            # TODO: try/except on KeyError here?
            try:
                blockhash = self._block_store.get_hash(self._browse_height)
                block = self._block_store.get_block(blockhash)
            except KeyError:
                draw_no_block()
                return

            draw_block(block)

            # TODO: draw transactions (transaction store?)
            # draw_transactions(state)

        else:
            draw_no_block()
