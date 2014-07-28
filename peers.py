#!/usr/bin/env python
import curses

import global_mod as g
import footer

def draw_window(state, window):
    window.clear()
    window.refresh()

    win_header = curses.newwin(3, 75, 0, 0)

    if 'peerinfo' in state:
        win_header.addstr(0, 1, "connected peers: " + str(len(state['peerinfo'])).ljust(10) + "            (UP/DOWN: scroll, P: refresh)", curses.A_BOLD)
        win_header.addstr(2, 1, "  Node IP                      Version                Recv      Sent", curses.A_BOLD + curses.color_pair(5))
        draw_peers(state)

    else:
        win_header.addstr(0, 1, "no peer information loaded", curses.A_BOLD + curses.color_pair(3))
        win_header.addstr(1, 1, "press 'P' to refresh", curses.A_BOLD)

    win_header.refresh()
    footer.draw_window(state)

def draw_peers(state):
    window_height = state['y'] - 4
    win_peers = curses.newwin(window_height, 75, 3, 0)

    offset = state['peerinfo_offset']

    for index in xrange(offset, offset+window_height):
        if index < len(state['peerinfo']):
            peer = state['peerinfo'][index]

            condition = (index == offset+window_height-1) and (index+1 < len(state['peerinfo']))
            condition = condition or ( (index == offset) and (index > 0) )

            if condition:
                # scrolling up or down is possible
                win_peers.addstr(index-offset, 3, "...")

            else:
                if peer['inbound']:
                    win_peers.addstr(index-offset, 1, 'I')

                elif 'syncnode' in peer:
                    if peer['syncnode']:
                        # syncnodes are outgoing only
                        win_peers.addstr(index-offset, 1, 'S')

                win_peers.addstr(index-offset, 3, peer['addr'])
                win_peers.addstr(index-offset, 32, peer['subver'].strip("/"))

                mbrecv = "% 7.1f" % ( float(peer['bytesrecv']) / 1048576 )
                mbsent = "% 7.1f" % ( float(peer['bytessent']) / 1048576 )

                win_peers.addstr(index-offset, 50, mbrecv + 'MB')
                win_peers.addstr(index-offset, 60, mbsent + 'MB')

    win_peers.refresh()
