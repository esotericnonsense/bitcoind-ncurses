#!/usr/bin/env python
import curses
import global_mod as g

splash_array = [
    "  BB            BB                                   BB",
    "  BB       BB   BB    BBBB    BBBB   BB  BB BB       BB",
    "  BBBBB        BBBB  BB     BB   BB      BBB BB   BBBBB",
    "  BB   BB  BB   BB   BB     BB   BB  BB  BB  BB  BB  BB",
    "  BBB  BB  BB   BB   BB     BB   BB  BB  BB  BB  BB  BB",
    "  BB BBB   BB    BB   BBBB    BBBB   BB  BB  BB    BBBB",
]

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_splash = curses.newwin(12, 76, 0, 0)

    color = curses.color_pair(0)
    if 'testnet' in state:
        if state['testnet']: color = curses.color_pair(2)
        else: color = curses.color_pair(1)

    y = 0
    while y < len(splash_array):
        x = 0
        while x < len(splash_array[y]):
            if splash_array[y][x] != " ":
                win_splash.addstr(y+1, x, " ", color + curses.A_REVERSE)
            x += 1
        y += 1

    output_string =  "                                    n     c     u     r     s     e     s "

    win_splash.addstr(8, 0, output_string, color + curses.A_BOLD)

    version = "[ " + g.version + " ]"
    output_string = version.rjust(74)

    win_splash.addstr(10, 0, output_string, curses.color_pair(3) + curses.A_BOLD)

    win_splash.refresh()
