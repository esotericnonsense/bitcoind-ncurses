#!/usr/bin/env python
import curses

import global_mod as g

def draw_window(state):
    win_footer = curses.newwin(1, 76, state['y']-1, 0)

    modes = ['monitor', 'wallet', 'peers', 'block', 'transaction', 'console', 'quit']
    x = 2
    for mode_string in modes:
        modifier = curses.A_BOLD
        if state['mode'] == mode_string:
            modifier += curses.A_REVERSE
        win_footer.addstr(0, x, " " + mode_string[0].upper(), modifier + curses.color_pair(5)) 
        win_footer.addstr(0, x+2, mode_string[1:] + " ", modifier)
        x += len(mode_string) + 4

    win_footer.refresh()
