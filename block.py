#!/usr/bin/env python
import curses, time, calendar

import global_mod as g
import getstr

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(4, 75, 0, 0)

    if 'blocks' in state:
        if 'browse_height' in state['blocks']:
            height = str(state['blocks']['browse_height'])
            if height in state['blocks']:
                blockdata = state['blocks'][height]
                color = curses.color_pair(1)
                if 'testnet' in state:
                    if state['testnet']: color = curses.color_pair(2)
                win_header.addstr(0, 1, "bitcoind-ncurses " + g.version + " [block view] (press 'G' to enter a block)", color + curses.A_BOLD)
                win_header.addstr(1, 1, "height: " + height.zfill(6) + " (LEFT/RIGHT: browse, HOME/END: quick browse, L: latest)", curses.A_BOLD)
                win_header.addstr(2, 1, "hash: " + blockdata['hash'], curses.A_BOLD)
                win_header.addstr(3, 1, str(blockdata['size']) + " bytes (" + str(blockdata['size']/1024) + " KB)       ", curses.A_BOLD)
                win_header.addstr(3, 52, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(blockdata['time'])), curses.A_BOLD)
                draw_transactions(state)
                state['blocks']['loaded'] = 1

        else:
            win_header.addstr(0, 1, "no block loaded", curses.A_BOLD)
            win_header.addstr(1, 1, "press 'G' to enter a block hash or height", curses.A_BOLD)
            win_header.addstr(2, 1, "or 'M' to return to monitor window", curses.A_BOLD)

    win_header.refresh()

def draw_transactions(state):
    height = str(state['blocks']['browse_height'])
    blockdata = state['blocks'][height]

    win_transactions = curses.newwin(16, 75, 4, 0)
    tx_count = len(blockdata['tx'])
    bytes_per_tx = blockdata['size'] / tx_count
    win_transactions.addstr(0, 1, "Transactions: " + "% 4d" % tx_count + " (" + str(bytes_per_tx) + " bytes/tx) (UP/DOWN: scroll, SPACE: view)", curses.A_BOLD)

    offset = state['blocks']['offset']

    for index in xrange(offset, offset+15):
        if index < len(blockdata['tx']):
            if index == state['blocks']['cursor']:
                win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)

            if (index == offset+14) and (index+1 < len(blockdata['tx'])):
                win_transactions.addstr(index+1-offset, 3, "... " + blockdata['tx'][index])
            elif (index == offset) and (index > 0):
                win_transactions.addstr(index+1-offset, 3, "... " + blockdata['tx'][index])
            else:
                win_transactions.addstr(index+1-offset, 3, blockdata['tx'][index])

    win_transactions.refresh()

def draw_input_window(state, window, rpc_queue):
    color = curses.color_pair(1)
    if 'testnet' in state:
        if state['testnet']: color = curses.color_pair(2)

    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses " + g.version + " [block input mode]", color + curses.A_BOLD)
    window.addstr(1, 1, "please enter block height or hash", curses.A_BOLD)
    window.addstr(2, 1, "or timestamp (accepted formats: YYYY-MM-DD hh:mm:ss, YYYY-MM-DD)", curses.A_BOLD)
    window.refresh()

    win_textbox = curses.newwin(1,67,4,1) # h,w,y,x
    entered_block = getstr.getstr(win_textbox)
    entered_block_timestamp = 0

    try:
        entered_block_time = time.strptime(entered_block, "%Y-%m-%d")
        entered_block_timestamp = calendar.timegm(entered_block_time)
    except: pass

    try: 
        entered_block_time = time.strptime(entered_block, "%Y-%m-%d %H:%M:%S")
        entered_block_timestamp = calendar.timegm(entered_block_time)
    except: pass

    if entered_block_timestamp:
        s = {'findblockbytimestamp': entered_block_timestamp} 
        rpc_queue.put(s)

        window.addstr(5, 1, "waiting for block (will stall here if not found)", color + curses.A_BOLD)
        window.refresh()
        state['mode'] = "block"

    elif len(entered_block) == 64:
        s = {'getblock': entered_block}
        rpc_queue.put(s)

        window.addstr(5, 1, "waiting for block (will stall here if not found)", color + curses.A_BOLD)
        window.refresh()
        state['mode'] = "block"

    elif (len(entered_block) < 7) and entered_block.isdigit() and (int(entered_block) <= state['blockcount']):
        if entered_block in state['blocks']:
            state['blocks']['browse_height'] = int(entered_block)
            state['mode'] = "block"
            draw_window(state, window)
        else:
            s = {'getblockhash': int(entered_block)}
            rpc_queue.put(s)

            window.addstr(5, 1, "waiting for block (will stall here if not found)", color + curses.A_BOLD)
            window.refresh()
            state['mode'] = "block"
            state['blocks']['browse_height'] = int(entered_block)

    else:
        window.addstr(5, 1, "not a valid hash, height, or timestamp format", color + curses.A_BOLD)
        window.refresh()

        time.sleep(2)

        window.clear()
        window.refresh()
        state['mode'] = "monitor"
