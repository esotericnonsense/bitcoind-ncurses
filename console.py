#!/usr/bin/env python
import curses, pprint

import global_mod as g
import getstr
import json

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(1, 76, 0, 0)

    win_header.addstr(0, 1, "G: enter command".rjust(72), curses.A_BOLD + curses.color_pair(5))
    win_header.refresh()

    if len(state['console']['rbuffer']):
        draw_buffer(state)

def draw_buffer(state):
    window_height = state['y'] - 3
    win_buffer = curses.newwin(window_height, state['x'], 1, 0)

    #TODO: reimplement and print JSON dicts in a more readable format
    lines = []
    for index in xrange(0,len(state['console']['rbuffer'])):
        command = state['console']['cbuffer'][index]
        lines.append(">> " + command)

        # rbuffer should always exist if cbuffer does
        item = state['console']['rbuffer'][index]
        # str.replace accounts for 'help' sending literal \n
        lines.extend( pprint.pformat(item,width=(state['x']-2)).replace('\\n','\n').splitlines() )

    numlines = len(lines)

    offset = state['console']['offset']

    for index in xrange(offset, offset+window_height):
        if index < numlines:
            if index == offset+window_height-1:
                win_buffer.addstr(window_height-(index-offset)-1, 1, "...")
            if index == offset and index:
                win_buffer.addstr(window_height-(index-offset)-1, 1, "...")
            else:
                line = lines[(numlines-1)-index]

                fmt = False
                if len(line) > 1:
                    if line[1] == ">":
                        if state['testnet']:
                            fmt = curses.color_pair(2) + curses.A_BOLD
                        else:
                            fmt = curses.color_pair(1) + curses.A_BOLD

                if len(line) > state['x']-1:
                    win_buffer.addstr(window_height-(index-offset)-1, 1, line[:(state['x']-5)] + ' ...', fmt)
                else:
                    win_buffer.addstr(window_height-(index-offset)-1, 1, line, fmt)
        elif index == offset and index: 
            win_buffer.addstr(window_height-(index-offset)-1, 1, "...")
 
    win_buffer.refresh()

def draw_input_box(state, window, rpcc):
    entered_command = getstr.getstr(state['x'], state['y']-2, 1) # w, y, x

    if entered_command == "":
        pass
    else:
        raw_params = entered_command.split()
        method = raw_params[0]

        # TODO: figure out how to encode properly for submission; this is hacky.
        params = []
        for raw_param in raw_params[1:]:
            if raw_param.isdigit():
                params.append(int(raw_param))
            elif raw_param == "false" or raw_param == "False":
                params.append(False)
            elif raw_param == "true" or raw_param == "True":
                params.append(True)
            else:
                try:
                    params.append(decimal.Decimal(raw_param))
                except:
                    params.append(raw_param)

        try:
            resp = rpcc.sync_request(method, *params)
            state['console']['rbuffer'].append(resp.result)
        except:
            state['console']['rbuffer'].append("ERROR")

        state['console']['cbuffer'].append("{}{}".format(method, tuple(params)))
        state['console']['offset'] = 0

        draw_window(state, window)
