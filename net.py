#!/usr/bin/env python
import curses, math

import global_mod as g

def draw_window(state, old_window):
    old_window.clear()
    old_window.refresh()
    window_height = state['y'] - 1
    window_width = state['x']
    window = curses.newwin(window_height, window_width, 0, 0)

    history = state['history']['getnettotals']

    sent_deltas = []
    recv_deltas = []

    index = 1
    while index < len(history):
        timedelta = history[index]['timemillis'] - history[index-1]['timemillis']
        recvdelta = history[index]['totalbytesrecv'] - history[index-1]['totalbytesrecv']
        sentdelta = history[index]['totalbytessent'] - history[index-1]['totalbytessent']

        recv_deltas.append(recvdelta*1000 // timedelta) 
        sent_deltas.append(sentdelta*1000 // timedelta) 

        index += 1

    if sent_deltas:
        chart_height = window_height - 2
        plot_height = chart_height // 2
        chart_width = window_width - 11

        if len(sent_deltas) > chart_width:
            sent_deltas = sent_deltas[-chart_width:]
            recv_deltas = recv_deltas[-chart_width:]

        color_sent = curses.color_pair(2)
        color_recv = curses.color_pair(1)
        max_sent = max(sent_deltas)
        max_recv = max(recv_deltas)
        max_total = max(max_sent, max_recv)

        if max_total > 0:
            if max_sent > 0:
                height = int(math.ceil((1.0 * plot_height * max_sent) / max_total))
                window.addstr(plot_height-height, 1, ("%0.1f" % (max_sent*1.0//1024)).rjust(6) + "K", curses.A_BOLD) 
            if max_recv > 0:
                height = int(math.ceil((1.0 * plot_height * max_recv) / max_total))
                window.addstr(plot_height+height, 1, ("%0.1f" % (max_recv*1.0//1024)).rjust(6) + "K", curses.A_BOLD) 

            index = 0
            while index < len(sent_deltas):
                if index < chart_width:
                    height = int(math.ceil((1.0 * plot_height * sent_deltas[index]) / max_total))
                    for y in range(0, height):
                        window.addch(plot_height-1-y, index+10, " ", color_sent + curses.A_REVERSE)

                    height = int(math.ceil((1.0 * plot_height * recv_deltas[index]) / max_total))
                    for y in range(0, height):
                        window.addch(plot_height+1+y, index+10, " ", color_recv + curses.A_REVERSE)
                index += 1

            recv_string = "Down: " + ("%0.1f" % (recv_deltas[-1]*1.0/1024)).rjust(7) + "KB/s"
            sent_string = "Up: " + ("%0.1f" % (sent_deltas[-1]*1.0/1024)).rjust(7) + "KB/s"
            total_string = "Total: " + ("%0.1f" % ((sent_deltas[-1] + recv_deltas[-1])*1.0/1024)).rjust(7) + "KB/s" 
            window.addstr(chart_height+1, window_width-1-18, total_string, curses.A_BOLD)
            window.addstr(chart_height+1, window_width-1-38, sent_string, curses.A_BOLD + color_sent)
            window.addstr(chart_height+1, window_width-1-58, recv_string, curses.A_BOLD + color_recv)

    window.refresh()
