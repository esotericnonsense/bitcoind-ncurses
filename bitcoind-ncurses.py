#!/usr/bin/env python

##
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
##
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, sys, threading, Queue, json, textwrap, ConfigParser
import argparse

# attrib: user1476056
# https://stackoverflow.com/questions/11303986/addstr-causes-getstr-to-return-on-signal
# re-implement at some point
def getstr(window, prompt = "> ", end_on_error = False):
    result = ""
    starty, startx = window.getyx()
    window.move(starty, 0)
    window.deleteln()
    window.addstr(prompt, curses.A_BOLD)
    window.refresh()
    window.keypad(True)

    starty, startx = window.getyx()
    endy, endx = window.getyx()
    maxy, maxx = window.getmaxyx()
    while True:
        try:
            selection = -1
            while (selection < 0 and end_on_error == False):
                selection = window.getch()
        except:
            e = sys.exc_info()[0]
            window.addstr("<p>Error: %s</p>" % e)
            break

        if (selection == curses.KEY_ENTER or selection == ord('\n')):
            break
        elif (selection == curses.KEY_BACKSPACE or selection == 127):
            cy, cx = window.getyx()
            if (cx == startx):
                # no more to backspace
                continue
            else:
                window.move(cy, cx-1)
                window.delch()
                endx -= 1
                cx -= 1
                result = result[:(cx - startx)] + result[(cx - startx + 1):]
                continue
        else:
            endy, endx = window.getyx()
            if (selection < 256 and endx+1 < maxx):
                result = result[:(endx - startx)] + chr(selection) + result[(endx - startx):]
                window.addstr(result[(endx - startx):])
                window.move(endy, endx+1)
                endy, endx = window.getyx()


    window.keypad(False)
    return result

def draw_block_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(3, 75, 0, 0)

    if 'block' in state:
        win_header.addstr(0, 1, "bitcoind-ncurses - block view", curses.color_pair(1) + curses.A_BOLD)
        win_header.addstr(1, 1, "hash: " + state['block']['hash'], curses.A_BOLD)
        draw_block_transactions(state)

    else:
        win_header.addstr(0, 1, "no block loaded", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'd' to return to main window", curses.A_BOLD)

    win_header.refresh()

def draw_block_transactions(state):
    win_transactions = curses.newwin(17, 75, 3, 0)
    win_transactions.addstr(0, 1, "transactions (UP/DOWN: scroll, RIGHT: view)", curses.A_BOLD)

    offset = state['block']['offset']

    for index in xrange(offset, offset+16):
        if index < len(state['block']['tx']):
            if index == state['block']['cursor']:
                win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)
            win_transactions.addstr(index+1-offset, 3, state['block']['tx'][index])

    win_transactions.refresh()

def draw_transaction_window(state, window):
    # TODO: add transaction locktime, add sequence to inputs
    window.clear()
    window.refresh()
    win_header = curses.newwin(3, 75, 0, 0)

    if 'tx' in state:
        win_header.addstr(0, 1, "bitcoind-ncurses - transaction view (press 'g' to enter a txid)", curses.color_pair(1) + curses.A_BOLD)
        win_header.addstr(1, 1, "txid: " + state['tx']['txid'], curses.A_BOLD)
        draw_transaction_inputs(state)
        draw_transaction_outputs(state)

    else:
        win_header.addstr(0, 1, "no transaction loaded", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'g' to enter a txid, or 'd' to return to main window", curses.A_BOLD)

    win_header.refresh()

def draw_transaction_input_window(state, window):
    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses - transaction input", curses.color_pair(1) + curses.A_BOLD)
    window.addstr(1, 1, "please type in txid as hex", curses.A_BOLD)
    window.refresh()
    win_textbox = curses.newwin(1,67,3,1) # h,w,y,x
    entered_txid = getstr(win_textbox)
    if len(entered_txid) == 64: # TODO: better checking for valid txid here
        s = {'txid': entered_txid}
        rpc_queue.put(s)
        window.addstr(5, 1, "waiting for transaction (will stall here if not found)", curses.color_pair(1) + curses.A_BOLD)
        state['mode'] = "transaction"
        window.refresh()
    else:
        window.addstr(5, 1, "not a valid txid", curses.color_pair(1) + curses.A_BOLD)
        window.refresh()
        time.sleep(2)
        window.clear()
        window.refresh()
        state['mode'] = "default"

def draw_transaction_inputs(state):
    win_inputs = curses.newwin(8, 75, 3, 0)
    win_inputs.addstr(0, 1, "inputs (UP/DOWN: select, RIGHT: view)", curses.A_BOLD)

    offset = state['tx']['offset']

    for index in xrange(offset, offset+7):
        if index < len(state['tx']['vin']):
            if 'txid' in state['tx']['vin'][index]:
                if index == (state['tx']['cursor']):
                    win_inputs.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)
                win_inputs.addstr(index+1-offset, 3, state['tx']['vin'][index]['txid'] + ":" + "%03d" % state['tx']['vin'][index]['vout'])
            elif 'coinbase' in state['tx']['vin'][index]:
                win_inputs.addstr(index+1-offset, 3, "coinbase " + state['tx']['vin'][index]['coinbase'])

    win_inputs.refresh()

def draw_transaction_outputs(state):
    win_outputs = curses.newwin(8, 75, 12, 0)
    if len(state['tx']['vout_string']) > 7:
        win_outputs.addstr(0, 1, "outputs (PGUP/PGDOWN: scroll)", curses.A_BOLD)
    else:
        win_outputs.addstr(0, 1, "outputs", curses.A_BOLD)

    offset = state['tx']['out_offset']

    for index in xrange(offset, offset+7):
        if index < len(state['tx']['vout_string']):
            win_outputs.addstr(index+1-offset, 1, state['tx']['vout_string'][index])
    win_outputs.refresh()

def draw_main_window(state, window):
    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses v0.0.4", curses.color_pair(1) + curses.A_BOLD)

    if 'version' in state:
        if state['testnet'] == 1:
            window.addstr(1, 1, "bitcoind v" + state['version'] + " (testnet)", curses.color_pair(2) + curses.A_BOLD)
        else:
            window.addstr(1, 1, "bitcoind v" + state['version'] + " ", curses.color_pair(1) + curses.A_BOLD)

    if 'peers' in state:
        window.addstr(0, 32, str(state['peers']) + " peers    ", curses.A_BOLD)

    if 'balance' in state:
        window.addstr(1, 32, "%0.8f" % state['balance'] + " BTC", curses.A_BOLD)

    if 'height' in state:
        window.addstr(3, 1, str(state['height']).zfill(6) + ": " + str(state['hash']))
        window.addstr(4, 1, str(state['size']) + " bytes (" + str(state['size']/1024) + " KB)       ")
        window.addstr(4, 38, "Timestamp: " + time.asctime(time.gmtime(state['time'])))

    if 'totalbytesrecv' in state:
        window.addstr(0, 57, "D: " + "% 10.2f" % (state['totalbytesrecv']*1.0/1048576) + " MB", curses.A_BOLD)
        window.addstr(1, 57, "U: " + "% 10.2f" % (state['totalbytessent']*1.0/1048576) + " MB", curses.A_BOLD)

    if 'lastblocktime' in state: # time ncurses noticed the block, not timestamp
        if 'time' in state:
            since_last_block_timestamp = time.time() - state['time']
            lastblockmins = int((time.time() - state['lastblocktime']) / 60)
            lastblocksecs = int((time.time() - state['lastblocktime']) % 60)
            if (lastblockmins > 0): window.addstr(6, 38, "Received " + str(lastblockmins) + "m " + str(lastblocksecs) + "s ago      ")
            else: window.addstr(6, 38, "Received " + str(lastblocksecs) + "s ago           ")
            if (since_last_block_timestamp > 3600*3):    # assume over 3 hours is syncing
                window.addstr(6, 64, "(syncing)", curses.color_pair(3))

            window.addstr(5, 38, "Now (UTC): " + time.asctime(time.gmtime(time.time())))
    window.addstr(8, 1, "Hotkeys: t (transaction viewer), b (block viewer), d (this screen)", curses.A_BOLD)
    window.addstr(9, 1, "         q (exit bitcoind-ncurses), g (manually enter txid)", curses.A_BOLD)

    window.refresh()

def input_loop(state, win):
    c = win.getch()

    if c == ord('q'):
        return 1

    if c == ord('d'):
        state['mode'] = "default"
        draw_main_window(state, win)

    if c == ord('t'):
        state['mode'] = "transaction"
        draw_transaction_window(state, win)

    if c == ord('g'):
        state['mode'] = "transaction-input"
        draw_transaction_input_window(state, win)

    if c == ord('b'):
        state['mode'] = "block"
        draw_block_window(state, win)

    if c == curses.KEY_DOWN:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] < (len(state['tx']['vin']) - 1):
                    state['tx']['cursor'] += 1
                    if (state['tx']['cursor'] - state['tx']['offset']) > 6:
                        state['tx']['offset'] += 1
                    draw_transaction_inputs(state)

        elif state['mode'] == "block":
            if 'block' in state:
                if state['block']['cursor'] < (len(state['block']['tx']) - 1):
                    state['block']['cursor'] += 1
                    if (state['block']['cursor'] - state['block']['offset']) > 15:
                        state['block']['offset'] += 1
                    draw_block_transactions(state)

    if c == curses.KEY_UP:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] > 0:
                    if (state['tx']['cursor'] - state['tx']['offset']) == 0:
                        state['tx']['offset'] -= 1
                    state['tx']['cursor'] -= 1
                    draw_transaction_inputs(state)

        elif state['mode'] == "block":
            if 'block' in state:
                if state['block']['cursor'] > 0:
                    if (state['block']['cursor'] - state['block']['offset']) == 0:
                        state['block']['offset'] -= 1
                    state['block']['cursor'] -= 1
                    draw_block_transactions(state)

    if c == curses.KEY_PPAGE:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['out_offset'] > 1:
                    state['tx']['out_offset'] -= 2
                    draw_transaction_outputs(state)

    if c == curses.KEY_NPAGE:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['out_offset'] < (len(state['tx']['vout_string']) - 7):
                    state['tx']['out_offset'] += 2
                    draw_transaction_outputs(state)

    if c == curses.KEY_RIGHT:
        # TODO: some sort of indicator that a transaction is loading
        if state['mode'] == "transaction":
            if 'tx' in state:
                if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]: 
                    s = {'txid': state['tx']['vin'][ state['tx']['cursor'] ]['txid']}
                    rpc_queue.put(s)

        if state['mode'] == "block":
            if 'block' in state: 
                s = {'txid': state['block']['tx'][ state['block']['cursor'] ]}
                rpc_queue.put(s)
                state['mode'] = "transaction"

    return 0

def rpc_loop(interface_queue, rpc_queue, config):
    # TODO: add some error checking for failed connection, json error, broken config
    rpcuser = config.get('rpc', 'rpcuser')
    rpcpassword = config.get('rpc', 'rpcpassword')
    rpcip = config.get('rpc', 'rpcip')
    rpcport = config.get('rpc', 'rpcport')

    rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    rpchandle = AuthServiceProxy(rpcurl, None, 500)

    last_blockcount = 0 # ensures block info is updated initially
    last_update = time.time() - 2
    while 1:
        try: s = rpc_queue.get(False)
        except: s = {}

        if 'stop' in s:
            break
        elif 'blockheight' in s:
            blockhash = rpchandle.getblockhash(s['blockheight'])
            blockinfo = rpchandle.getblock(blockhash)
            interface_queue.put(blockinfo)
            last_blockcount = cur_blockcount
        elif 'txid' in s:
            raw_tx = rpchandle.getrawtransaction(s['txid'])
            decoded_tx = rpchandle.decoderawtransaction(raw_tx)
            interface_queue.put(decoded_tx)

        if (time.time() - last_update) > 2:
            info = rpchandle.getinfo()
            interface_queue.put(info)

            nettotals = rpchandle.getnettotals()
            interface_queue.put(nettotals)

            walletinfo = rpchandle.getwalletinfo()
            interface_queue.put(walletinfo)

            cur_blockcount = info['blocks']
            if (cur_blockcount != last_blockcount): # minimise RPC calls
                lastblocktime = {'lastblocktime': time.time()}
                interface_queue.put(lastblocktime)

                blockhash = rpchandle.getblockhash(cur_blockcount)
                blockinfo = rpchandle.getblock(blockhash)
                interface_queue.put(blockinfo)
                last_blockcount = cur_blockcount

            last_update = time.time()

        time.sleep(0.05) # TODO: investigate a better way to idle CPU

def process_queue(state, window, interface_queue):
    try: s = interface_queue.get(False)
    except Queue.Empty: s = {}

    if 'connections' in s:
        state['version'] = str(s['version'] / 1000000)
        state['version'] += '.' + str((s['version'] % 1000000) / 10000)
        state['version'] += '.' + str((s['version'] % 10000) / 100)
        state['version'] += '.' + str((s['version'] % 100))
        if s['testnet'] == True:
            state['testnet'] = 1
        else:
            state['testnet'] = 0
        state['peers'] = s['connections']

    elif 'balance' in s:
        state['balance'] = s['balance']

    elif 'size' in s:
        state['height'] = s['height']
        state['hash'] = s['hash']
        state['size'] = s['size']
        state['time'] = s['time']

        state['block'] = { # TODO: sort out this utter mess
            'height': s['height'],
            'hash': s['hash'],
            'size': s['size'],
            'time': s['time'],
            'tx': s['tx'],
            'cursor': 0,
            'offset': 0
        }

        if state['mode'] == "default":
            draw_main_window(state, window)
        if state['mode'] == "block":
            draw_block_window(state, window)

    elif 'totalbytesrecv' in s:
        state['totalbytesrecv'] = s['totalbytesrecv']
        state['totalbytessent'] = s['totalbytessent']

    elif 'lastblocktime' in s:
        state['lastblocktime'] = s['lastblocktime']

    elif 'txid' in s:
        state['tx'] = {
            'txid': s['txid'],
            'vin': [],
            'vout_string': [],
            'cursor': 0,
            'offset': 0,
            'out_offset': 0
        }

        for vin in s['vin']:
            if 'coinbase' in vin:
                state['tx']['vin'].append({'coinbase':  vin['coinbase']})
            elif 'txid' in vin:
                state['tx']['vin'].append({'txid': vin['txid'], 'vout': vin['vout']})

        for vout in s['vout']:
            if 'value' in vout:
                buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']
                state['tx']['vout_string'].extend(textwrap.wrap(buffer_string,73)) # change this to scale with window ?

        if state['mode'] == "transaction":
            draw_transaction_window(state, window)

def check_window_size(window):
    if (window.getmaxyx()[0] < 20) or (window.getmaxyx()[1] < 75):
        curses.nocbreak()
        curses.endwin()
        sys.stderr.write('Screen size is too small (must be at least 75x20)\n')
        sys.exit(1)

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

def interface_loop():
    win = init_curses()

    # coinbase testnet transaction for debugging
    #s = {'txid': "cfb8bc436ca1d8b8b2d324a9cb2ef097281d2d8b54ba4239ce447b31b8757df2"}
    # tx with 1001 inputs, 1002 outputs 
    #s = {'txid': 'e1dc93e7d1ee2a6a13a9d54183f91a5ae944297724bee53db00a0661badc3005'}
    #rpc_queue.put(s)

    state = { 'mode': "default" }

    while 1:
        check_window_size(win)
        process_queue(state, win, interface_queue)

        if state['mode'] == "default":
            if (int(time.time() * 1000) % 1000) < 100: # hackish idle
              draw_main_window(state, win)

        if input_loop(state, win): break

        time.sleep(0.05) # TODO: base updates on interrupts to avoid needless polling

    curses.nocbreak()
    curses.endwin()
    rpc_queue.put({ 'stop': 1 })

if __name__ == '__main__':
    interface_queue = Queue.Queue()
    rpc_queue = Queue.Queue()

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="path to config file [bitcoind-ncurses.conf]",
                        default="bitcoind-ncurses.conf")
    args = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(args.config)

    rpc_thread = threading.Thread(target=rpc_loop, args = (interface_queue, rpc_queue, config))
    rpc_thread.daemon = True
    rpc_thread.start()

    interface_loop()

    rpc_thread.join()
