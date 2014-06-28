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

    for i in xrange(0, 16):
        if i < len(state['block']['tx']):
            if i == state['block']['cursor']:
                win_transactions.addstr(i+1, 1, ">", curses.A_REVERSE + curses.A_BOLD)
            win_transactions.addstr(i+1, 3, state['block']['tx'][i])

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
        json_q.put(s)
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

    for i in xrange(0, 7):
        if i < len(state['tx']['vin']):
            if 'txid' in state['tx']['vin'][i]:
                if i == state['tx']['cursor']:
                    win_inputs.addstr(i+1, 1, ">", curses.A_REVERSE + curses.A_BOLD)
                win_inputs.addstr(i+1, 3, state['tx']['vin'][i]['txid'] + ":" + "%03d" % state['tx']['vin'][i]['vout'])
            elif 'coinbase' in state['tx']['vin'][i]:
                win_inputs.addstr(i+1, 3, "coinbase " + state['tx']['vin'][i]['coinbase'])

    win_inputs.refresh()

def draw_transaction_outputs(state):
    win_outputs = curses.newwin(8, 75, 12, 0)
    win_outputs.addstr(0, 1, "outputs (not scrollable yet)", curses.A_BOLD)
    for i in xrange(0, 7):
        if i < len(state['tx']['vout_string']):
            win_outputs.addstr(i+1, 1, state['tx']['vout_string'][i])
    win_outputs.refresh()

def input_loop(state, win, c):
    if c == ord('q'):
        return 1

    if c == ord('d'):
        win.clear()
        state['mode'] = "default"

    if c == ord('t'):
        state['mode'] = "transaction"
        draw_transaction_window(state, win)

    if c == ord('g'):
        state['mode'] = "transaction-input"
        draw_transaction_input_window(state, win)

    if c == ord('b'):
        win.clear()
        win.refresh()
        state['mode'] = "block"
        draw_block_window(state, win)

    if c == curses.KEY_DOWN:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] < (len(state['tx']['vin']) - 1):
                    state['tx']['cursor'] += 1
                    draw_transaction_inputs(state)

        elif state['mode'] == "block":
            if 'block' in state:
                if state['block']['cursor'] < (len(state['block']['tx']) - 1):
                    state['block']['cursor'] += 1
                    draw_block_transactions(state)

    if c == curses.KEY_UP:
        if state['mode'] == "transaction":
            if 'tx' in state:
                if state['tx']['cursor'] > 0:
                    state['tx']['cursor'] -= 1
                    draw_transaction_inputs(state)

        elif state['mode'] == "block":
            if 'block' in state:
                if state['block']['cursor'] > 0:
                    state['block']['cursor'] -= 1
                    draw_block_transactions(state)

    if c == curses.KEY_RIGHT:
        # TODO: some sort of indicator that a transaction is loading
        if state['mode'] == "transaction":
            if 'tx' in state:
                if 'txid' in state['tx']['vin'][ state['tx']['cursor'] ]: 
                    s = {'txid': state['tx']['vin'][ state['tx']['cursor'] ]['txid']}
                    json_q.put(s)

        if state['mode'] == "block":
            if 'block' in state: 
                s = {'txid': state['block']['tx'][ state['block']['cursor'] ]}
                json_q.put(s)
                state['mode'] = "transaction"

    return 0

def rpc_loop(ncurses_q, json_q, config):
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
        try: s = json_q.get(False)
        except: s = {}

        if 'stop' in s:
            break
        elif 'blockheight' in s:
            blockhash = rpchandle.getblockhash(s['blockheight'])
            blockinfo = rpchandle.getblock(blockhash)
            ncurses_q.put(blockinfo)
            last_blockcount = cur_blockcount
        elif 'txid' in s:
            raw_tx = rpchandle.getrawtransaction(s['txid'])
            decoded_tx = rpchandle.decoderawtransaction(raw_tx)
            ncurses_q.put(decoded_tx)

        if (time.time() - last_update) > 2:
            info = rpchandle.getinfo()
            ncurses_q.put(info)

            nettotals = rpchandle.getnettotals()
            ncurses_q.put(nettotals)

            walletinfo = rpchandle.getwalletinfo()
            ncurses_q.put(walletinfo)

            cur_blockcount = info['blocks']
            if (cur_blockcount != last_blockcount): # minimise RPC calls
                lastblocktime = {'lastblocktime': time.time()}
                ncurses_q.put(lastblocktime)

                blockhash = rpchandle.getblockhash(cur_blockcount)
                blockinfo = rpchandle.getblock(blockhash)
                ncurses_q.put(blockinfo)
                last_blockcount = cur_blockcount

            last_update = time.time()
            time.sleep(0.5) # minimise RPC calls

def ncurses_loop():
    win = curses.initscr()
    curses.noecho() # prevents user input from being echoed
    # curses.cbreak() # is this actually necessary or useful?
    curses.curs_set(0) # make cursor invisible

    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    win.nodelay(1) # TODO: remove once fully interrupt based
    win.keypad(1) # interpret arrow keys, etc

    # random testnet transaction for debugging
    # s = {'txid': "465b8af08124a1d8fffc6d8320de9d5fa4eb25ba7b0b4f3add5e0f8793c8fc10"}
    # coinbase testnet transaction for debugging
    # s = {'txid': "cfb8bc436ca1d8b8b2d324a9cb2ef097281d2d8b54ba4239ce447b31b8757df2"}
    # json_q.put(s)

    state = { 'mode': "default" }

    while 1:
        # die if window too small
        if (win.getmaxyx()[0] < 20) or (win.getmaxyx()[1] < 75):
            # curses.nocbreak()
            curses.endwin()
            sys.stderr.write('Screen size is too small (must be at least 75x20)\n')
            sys.exit(1)
            break

        # process queue
        try: s = ncurses_q.get(False)
        except: s = {}

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

            state['block'] = { # this looks rather silly, and that's because it is; fix later
                'height': s['height'],
                'hash': s['hash'],
                'size': s['size'],
                'time': s['time'],
                'tx': s['tx'],
                'cursor': 0
            }

            if state['mode'] == "block":
                draw_block_window(state, win)

        elif 'totalbytesrecv' in s:
            state['totalbytesrecv'] = s['totalbytesrecv']
            state['totalbytessent'] = s['totalbytessent']

        elif 'lastblocktime' in s:
            state['lastblocktime'] = s['lastblocktime']

        elif 'txid' in s:
            state['tx'] = { 'txid': s['txid'], 'vin': [], 'vout_string': [], 'cursor': 0 }

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
                draw_transaction_window(state, win)

        # draw to screen, default mode
        if state['mode'] == "default":
            win.addstr(0, 1, "bitcoind-ncurses v0.0.4", curses.color_pair(1) + curses.A_BOLD)

            if 'version' in state:
                if state['testnet'] == 1:
                    win.addstr(1, 1, "bitcoind v" + state['version'] + " (testnet)", curses.color_pair(2) + curses.A_BOLD)
                else:
                    win.addstr(1, 1, "bitcoind v" + state['version'] + " ", curses.color_pair(1) + curses.A_BOLD)

            if 'peers' in state:
                win.addstr(0, 32, str(state['peers']) + " peers    ", curses.A_BOLD)

            if 'balance' in state:
                win.addstr(1, 32, "%0.8f" % state['balance'] + " BTC", curses.A_BOLD)

            if 'height' in state:
                win.addstr(3, 1, str(state['height']).zfill(6) + ": " + str(state['hash']))
                win.addstr(4, 1, str(state['size']) + " bytes (" + str(state['size']/1024) + " KB)       ")
                win.addstr(4, 38, "Timestamp: " + time.asctime(time.gmtime(state['time'])))

            if 'totalbytesrecv' in state:
                win.addstr(0, 57, "D: " + "% 10.2f" % (state['totalbytesrecv']*1.0/1048576) + " MB", curses.A_BOLD)
                win.addstr(1, 57, "U: " + "% 10.2f" % (state['totalbytessent']*1.0/1048576) + " MB", curses.A_BOLD)

            if 'lastblocktime' in state: # time ncurses noticed the block, not timestamp
                if 'time' in state:
                    since_last_block_timestamp = time.time() - state['time']
                    lastblockmins = int((time.time() - state['lastblocktime']) / 60)
                    lastblocksecs = int((time.time() - state['lastblocktime']) % 60)
                    if (lastblockmins > 0): win.addstr(6, 38, "Received " + str(lastblockmins) + "m " + str(lastblocksecs) + "s ago      ")
                    else: win.addstr(6, 38, "Received " + str(lastblocksecs) + "s ago           ")
                    if (since_last_block_timestamp > 3600*3):    # assume over 3 hours is syncing
                        win.addstr(6, 64, "(syncing)", curses.color_pair(3))

            win.addstr(5, 38, "Now (UTC): " + time.asctime(time.gmtime(time.time())))
            win.addstr(8, 1, "Hotkeys: t (transaction viewer), b (block viewer), d (this screen)", curses.A_BOLD)
            win.addstr(9, 1, "         q (exit bitcoind-ncurses), g (manually enter txid)", curses.A_BOLD)

            win.refresh()

        # take input, quit if needed
        c = win.getch()
        if input_loop(state, win, c): break

        # delay to avoid excessive CPU usage
        # TODO: base updates on interrupts to avoid needless polling
        time.sleep(0.1)

    # loop was broken, safely quit ncurses
    curses.nocbreak()
    curses.endwin()
    json_q.put({ 'stop': 1 })

if __name__ == '__main__':

    ncurses_q = Queue.Queue()
    json_q = Queue.Queue()

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="path to config file [bitcoind-ncurses.conf]",
                        default="bitcoind-ncurses.conf")
    args = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(args.config)

    thread1 = threading.Thread(target=rpc_loop, args = (ncurses_q, json_q, config))
    thread1.daemon = True
    thread1.start()

    ncurses_loop()
