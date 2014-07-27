#!/usr/bin/env python
import curses, sys, time

import monitor
import process
import hotkey
import splash

def check_window_size(interface_queue, state, window, min_y, min_x):
    # TODO: use SIGWINCH interrupt
    new_x = window.getmaxyx()[1]
    new_y = window.getmaxyx()[0]
    if (new_y < min_y) or (new_x < min_x):
        interface_queue.put({ 'stop': "Window is too small - must be at least " + str(min_x) + "x" + str(min_y)}) 
    elif 'x' in state and 'y' in state:
        if state['x'] != new_x or state['y'] != new_y:
            state['x'] = new_x
            state['y'] = new_y
            interface_queue.put({'resize': 1})
    else:
        state['x'] = new_x
        state['y'] = new_y

def init_curses():
    window = curses.initscr()
    curses.noecho() # prevents user input from being echoed
    curses.cbreak() # is this actually necessary or useful?
    curses.curs_set(0) # make cursor invisible

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    window.nodelay(1) # TODO: remove once fully interrupt based
    window.keypad(1) # interpret arrow keys, etc

    return window

def loop(interface_queue, rpc_queue):
    window = init_curses()

    state = {
        'mode': "splash",
        'blocks': { 'cursor': 0, 'offset': 0 },
        'networkhashps': {},
        'console': { 'cbuffer': [], 'rbuffer': [], 'offset': 0 }
    }

    splash.draw_window(state, window)

    while 1:
        check_window_size(interface_queue, state, window, 10, 75) # min_y, min_x
        error_message = process.queue(state, window, interface_queue)
        if error_message:
            break # ends if stop command sent by rpc

        if state['mode'] == "monitor":
            if (int(time.time() * 1000) % 1000) < 100: # hackish idle
              monitor.draw_window(state, window)

        if hotkey.check(state, window, rpc_queue): # poll for user input
            break # returns 1 when quit key is pressed

        time.sleep(0.05) # TODO: base updates on interrupts to avoid needless polling

    curses.nocbreak()
    curses.endwin()
    rpc_queue.put({ 'stop': True })
    
    if error_message:
        sys.stderr.write("bitcoind-ncurses encountered an error\n")
        sys.stderr.write("Message: " + error_message + "\n")
