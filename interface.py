#!/usr/bin/env python
import curses
import sys
import gevent

import monitor
import process
import hotkey
import splash
import footer

def check_window_size(interface_queue, state, window, min_y, min_x):
    # TODO: use SIGWINCH interrupt
    if (state['y'], state['x']) != window.getmaxyx():
        new_y, new_x = window.getmaxyx()

        if (new_y < min_y) or (new_x < min_x):
            interface_queue.put({ 'stop': "Window is too small - must be at least " + str(min_x) + "x" + str(min_y)})

        if (state['y'], state['x']) != (-1, -1): # initialized
            interface_queue.put({'resize': 1})

        state['x'] = new_x
        state['y'] = new_y

def init_curses():
    window = curses.initscr()
    curses.noecho() # prevents user input from being echoed
    curses.curs_set(0) # make cursor invisible

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    window.timeout(50)
    window.keypad(1) # interpret arrow keys, etc

    return window

def init_state():
    state = {
        'mode': "splash",
        'blocks': { 'cursor': 0, 'offset': 0 },
        'networkhashps': {},
        'estimatefee': {},
        'console': { 'cbuffer': [], 'rbuffer': [], 'offset': 0 },
        'x': -1,
        'y': -1,
        'history': { 'getnettotals': [] }
    }

    return state

def loop(block_viewer, state, window, interface_queue, rpcc, poller):
    iterations = 0
    while 1:
        check_window_size(interface_queue, state, window, 12, 75) # min_y, min_x
        error_message = process.queue(state, window, interface_queue)
        if error_message:
            return error_message # ends if stop command sent by rpc

        gevent.sleep(0.0001) # TODO: Can we kill this?

        if state['mode'] == "monitor":
            if not iterations % 20:
                monitor.draw_window(state, window)
                footer.draw_window(state)

        if hotkey.check(block_viewer, state, window, rpcc, poller): # poll for user input
            break # returns 1 when quit key is pressed

        iterations += 1

    return False

def main(block_viewer, window, interface_queue, rpcc, poller, initial_mode=None):
    error_message = False
    rpcc.request("getnetworkinfo")
    rpcc.request("getblockchaininfo")
    try:
        state = init_state()
        splash.draw_window(state, window)
        check_window_size(interface_queue, state, window, 12, 75) # min_y, min_x
        if initial_mode:
            hotkey.change_mode(state, window, initial_mode, poller)
        error_message = loop(block_viewer, state, window, interface_queue, rpcc, poller)
    finally: # restore sane terminal state, end RPC thread
        curses.nocbreak()
        curses.endwin()
    
        if error_message:
            sys.stderr.write("bitcoind-ncurses encountered an error\n")
            sys.stderr.write("Message: " + error_message + "\n")
