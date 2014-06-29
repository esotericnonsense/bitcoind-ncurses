#!/usr/bin/env python

##
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
##
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, sys, threading, Queue, json, textwrap, ConfigParser
import argparse

version = "v0.0.5"

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
    win_header = curses.newwin(4, 75, 0, 0)

    if 'blocks' in state:
        if 'browse_height' in state['blocks']:
            height = str(state['blocks']['browse_height'])
            if height in state['blocks']:
                blockdata = state['blocks'][height]
                win_header.addstr(0, 1, "bitcoind-ncurses " + version + " [block view]", curses.color_pair(1) + curses.A_BOLD)
                win_header.addstr(1, 1, "height: " + height.zfill(6) + " (LEFT/RIGHT: browse, L: go to latest)", curses.A_BOLD)
                win_header.addstr(2, 1, "hash: " + blockdata['hash'], curses.A_BOLD)
                win_header.addstr(3, 1, str(blockdata['size']) + " bytes (" + str(blockdata['size']/1024) + " KB)       ", curses.A_BOLD)
                win_header.addstr(3, 47, time.asctime(time.gmtime(blockdata['time'])), curses.A_BOLD)
                draw_block_transactions(state)
                state['blocks']['loaded'] = 1

        else:
            win_header.addstr(0, 1, "no block loaded", curses.A_BOLD)
            win_header.addstr(1, 1, "press 'D' to return to main window", curses.A_BOLD)

    win_header.refresh()

def draw_block_transactions(state):
    height = str(state['blocks']['browse_height'])
    blockdata = state['blocks'][height]

    win_transactions = curses.newwin(16, 75, 4, 0)
    win_transactions.addstr(0, 1, "Transactions:" + "% 4d" % len(blockdata['tx']) + " (UP/DOWN: scroll, SPACE: view)", curses.A_BOLD)

    offset = state['blocks']['offset']

    for index in xrange(offset, offset+15):
        if index < len(blockdata['tx']):
            if index == state['blocks']['cursor']:
                win_transactions.addstr(index+1-offset, 1, ">", curses.A_REVERSE + curses.A_BOLD)
            win_transactions.addstr(index+1-offset, 3, blockdata['tx'][index])

    win_transactions.refresh()

def draw_transaction_window(state, window):
    # TODO: add transaction locktime, add sequence to inputs
    window.clear()
    window.refresh()
    win_header = curses.newwin(3, 75, 0, 0)

    if 'tx' in state:
        win_header.addstr(0, 1, "bitcoind-ncurses " + version + " [transaction mode] (press 'G' to enter a txid)", curses.color_pair(1) + curses.A_BOLD)
        win_header.addstr(1, 1, "txid: " + state['tx']['txid'], curses.A_BOLD)
        draw_transaction_inputs(state)
        draw_transaction_outputs(state)

    else:
        win_header.addstr(0, 1, "no transaction loaded", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'G' to enter a txid, or 'D' to return to main window", curses.A_BOLD)

    win_header.refresh()

def draw_transaction_input_window(state, window):
    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses " + version + " [transaction input mode]", curses.color_pair(1) + curses.A_BOLD)
    window.addstr(1, 1, "please enter txid", curses.A_BOLD)
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
    win_inputs.addstr(0, 1, "inputs (UP/DOWN: select, SPACE: view)", curses.A_BOLD)

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
    # TODO: only draw parts that actually changed
    window.clear()
    window.addstr(0, 1, "bitcoind-ncurses " + version, curses.color_pair(1) + curses.A_BOLD)

    if 'version' in state:
        if state['testnet'] == 1:
            window.addstr(1, 1, "bitcoind v" + state['version'] + " (testnet)", curses.color_pair(2) + curses.A_BOLD)
        else:
            window.addstr(1, 1, "bitcoind v" + state['version'] + " ", curses.color_pair(1) + curses.A_BOLD)

    if 'peers' in state:
        window.addstr(0, 32, str(state['peers']) + " peers    ", curses.A_BOLD)

    if 'balance' in state:
        window.addstr(1, 32, "%0.8f" % state['balance'] + " BTC", curses.A_BOLD)

    if 'blockcount' in state:
        height = str(state['blockcount'])
        if height in state['blocks']:
            blockdata = state['blocks'][str(height)]

            window.addstr(3, 1, height.zfill(6) + ": " + str(blockdata['hash']))
            window.addstr(4, 1, str(blockdata['size']) + " bytes (" + str(blockdata['size']/1024) + " KB)       ")
            window.addstr(4, 38, "Timestamp: " + time.asctime(time.gmtime(blockdata['time'])))

            lastblockmins = int((time.time() - state['lastblocktime']) / 60)
            lastblocksecs = int((time.time() - state['lastblocktime']) % 60)

            if (lastblockmins > 0): window.addstr(6, 38, "Received " + str(lastblockmins) + "m " + str(lastblocksecs) + "s ago      ")
            else: window.addstr(6, 38, "Received " + str(lastblocksecs) + "s ago           ")

            since_last_block_timestamp = time.time() - blockdata['time']
            if (since_last_block_timestamp > 3600*3):    # assume over 3 hours is syncing
                window.addstr(6, 64, "(syncing)", curses.color_pair(3))

            window.addstr(5, 38, "Now (UTC): " + time.asctime(time.gmtime(time.time())))

    if 'totalbytesrecv' in state:
        window.addstr(0, 57, "D: " + "% 10.2f" % (state['totalbytesrecv']*1.0/1048576) + " MB", curses.A_BOLD)
        window.addstr(1, 57, "U: " + "% 10.2f" % (state['totalbytessent']*1.0/1048576) + " MB", curses.A_BOLD)


    window.addstr(8, 1, "Hotkeys: T (transaction viewer), B (block viewer), D (this screen)", curses.A_BOLD)
    window.addstr(9, 1, "         Q (exit bitcoind-ncurses), G (manually enter txid)", curses.A_BOLD)

    window.refresh()

def input_loop(state, window):
    c = window.getch()

    if c == ord('q') or c == ord('Q'):
        return 1

    if c == ord('d') or c == ord('D'):
        state['mode'] = "default"
        draw_main_window(state, window)

    if c == ord('t') or c == ord('T'):
        state['mode'] = "transaction"
        draw_transaction_window(state, window)

    if c == ord('g') or c == ord('G'):
        state['mode'] = "transaction-input"
        draw_transaction_input_window(state, window)

    if c == ord('b') or c == ord('B'):
        state['mode'] = "block"
        draw_block_window(state, window)

    if c == ord('l') or c == ord('L'):
        if state['mode'] == "block":
            if 'blockcount' in state:
                state['blocks']['browse_height'] = state['blockcount']
                if 'browse_height' not in state['blocks']:
                    s = {'getblockhash': state['blocks']['browse_height']}
                    rpc_queue.put(s)
                else:
                    draw_block_window(state, window)

    if c == curses.KEY_DOWN:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] < (len(state['tx']['vin']) - 1):
                    state['tx']['cursor'] += 1
                    if (state['tx']['cursor'] - state['tx']['offset']) > 6:
                        state['tx']['offset'] += 1
                    draw_transaction_inputs(state)

        elif state['mode'] == "block":
            if 'blocks' in state:
                height = str(state['blocks']['browse_height'])
                blockdata = state['blocks'][height]
                if state['blocks']['cursor'] < (len(blockdata['tx']) - 1):
                    state['blocks']['cursor'] += 1
                    if (state['blocks']['cursor'] - state['blocks']['offset']) > 14:
                        state['blocks']['offset'] += 1
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
            if 'blocks' in state:
                if state['blocks']['cursor'] > 0:
                    if (state['blocks']['cursor'] - state['blocks']['offset']) == 0:
                        state['blocks']['offset'] -= 1
                    state['blocks']['cursor'] -= 1
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

    if c == ord(' '):
        # TODO: some sort of indicator that a transaction is loading
        if state['mode'] == "transaction":
            if 'tx' in state:
                if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]: 
                    s = {'txid': state['tx']['vin'][ state['tx']['cursor'] ]['txid']}
                    rpc_queue.put(s)

        if state['mode'] == "block":
            if 'blocks' in state:
                height = str(state['blocks']['browse_height'])
                blockdata = state['blocks'][height]
                s = {'txid': blockdata['tx'][ state['blocks']['cursor'] ]}
                rpc_queue.put(s)
                state['mode'] = "transaction"

    if c == curses.KEY_LEFT:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) > 0:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] -= 1
                        if state['blocks']['browse_height'] in state['blocks']:
                            draw_block_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    if c == curses.KEY_RIGHT:
        if state['mode'] == "block":
            if 'blocks' in state:
                if (state['blocks']['browse_height']) < state['blockcount']:
                    if state['blocks']['loaded'] == 1:
                        state['blocks']['loaded'] = 0
                        state['blocks']['browse_height'] += 1
                        if state['blocks']['browse_height'] in state['blocks']:
                            draw_block_window(state, window)
                        else:
                            s = {'getblockhash': state['blocks']['browse_height']}
                            rpc_queue.put(s)

    return 0

def init_rpc(config):
    rpcuser = config.get('rpc', 'rpcuser')
    rpcpassword = config.get('rpc', 'rpcpassword')
    rpcip = config.get('rpc', 'rpcip')
    rpcport = config.get('rpc', 'rpcport')

    rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
    rpchandle = AuthServiceProxy(rpcurl, None, 500)

    return rpchandle

def rpc_loop(interface_queue, rpc_queue, config):
    # TODO: add some error checking for failed connection, json error, broken config
    rpchandle = init_rpc(config)

    last_update = time.time() - 2

    info = rpchandle.getinfo()
    interface_queue.put({'getinfo': info})

    prev_blockcount = 0
    while 1:
        try: s = rpc_queue.get(False)
        except Queue.Empty: s = {}

        if 'stop' in s:
            break
        elif 'getblockhash' in s:
            blockhash = rpchandle.getblockhash(s['getblockhash'])
            block = rpchandle.getblock(blockhash)
            interface_queue.put({'block': block})
        elif 'txid' in s:
            raw_tx = rpchandle.getrawtransaction(s['txid'])
            decoded_tx = rpchandle.decoderawtransaction(raw_tx)
            interface_queue.put(decoded_tx)

        if (time.time() - last_update) > 2:
            nettotals = rpchandle.getnettotals()
            connectioncount = rpchandle.getconnectioncount()
            blockcount = rpchandle.getblockcount()
            balance = rpchandle.getbalance()

            interface_queue.put({'getnettotals' : nettotals})
            interface_queue.put({'getconnectioncount' : connectioncount})
            interface_queue.put({'getblockcount' : blockcount})
            interface_queue.put({'getbalance' : balance})

            if (prev_blockcount != blockcount): # minimise RPC calls
                prev_blockcount = blockcount

                lastblocktime = {'lastblocktime': time.time()}
                interface_queue.put(lastblocktime)

                blockhash = rpchandle.getblockhash(blockcount)
                block = rpchandle.getblock(blockhash)
                interface_queue.put({'block': block})

            last_update = time.time()

        time.sleep(0.05) # TODO: investigate a better way to idle CPU

def process_queue(state, window, interface_queue):
    try: s = interface_queue.get(False)
    except Queue.Empty: s = {}

    if 'getinfo' in s:
        state['version'] = str(s['getinfo']['version'] / 1000000)
        state['version'] += '.' + str((s['getinfo']['version'] % 1000000) / 10000)
        state['version'] += '.' + str((s['getinfo']['version'] % 10000) / 100)
        state['version'] += '.' + str((s['getinfo']['version'] % 100))
        if s['getinfo']['testnet'] == True:
            state['testnet'] = 1
        else:
            state['testnet'] = 0
        state['peers'] = s['getinfo']['connections']

    elif 'getblockcount' in s:
        state['blockcount'] = s['getblockcount']
        if 'browse_height' not in state['blocks']:
            state['blocks']['browse_height'] = state['blockcount']

    elif 'getbalance' in s:
        state['balance'] = s['getbalance']

    elif 'block' in s:
        height = str(s['block']['height'])

        state['blocks'][height] = s['block']
        state['blocks']['cursor'] = 0
        state['blocks']['offset'] = 0

        if state['mode'] == "default":
            draw_main_window(state, window)
        if state['mode'] == "block":
            draw_block_window(state, window)

    elif 'getnettotals' in s:
        state['totalbytesrecv'] = s['getnettotals']['totalbytesrecv']
        state['totalbytessent'] = s['getnettotals']['totalbytessent']

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

    state = {
        'mode': "default",
        'blocks': {}
    }

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
