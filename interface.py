#!/usr/bin/env python
import curses, sys, time

import monitor
import process

def check_window_size(window, y, x):
    if (window.getmaxyx()[0] < y) or (window.getmaxyx()[1] < x):
        curses.nocbreak()
        curses.endwin()
        sys.stderr.write("Window is too small - must be at least " + str(x) + "x" + str(y) +"\n")
        sys.exit(1) # this is harsh, need to die gracefully

def init_curses():
    window = curses.initscr()
    curses.noecho() # prevents user input from being echoed
    curses.cbreak() # is this actually necessary or useful?
    curses.curs_set(0) # make cursor invisible

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    window.nodelay(1) # TODO: remove once fully interrupt based
    window.keypad(1) # interpret arrow keys, etc

    return window

def loop(interface_queue, rpc_queue):
    window = init_curses()

    state = {
        'mode': "monitor",
        'blocks': {}
    }

    while 1:
        check_window_size(window, 20, 75) # y, x
        process.queue(state, window, interface_queue)

        if state['mode'] == "monitor":
            if (int(time.time() * 1000) % 1000) < 100: # hackish idle
              monitor.draw_window(state, window)

        if process.user_input(state, window, rpc_queue):
            break # returns 1 when quit key is pressed

        time.sleep(0.05) # TODO: base updates on interrupts to avoid needless polling

    curses.nocbreak()
    curses.endwin()
    rpc_queue.put({ 'stop': 1 })
