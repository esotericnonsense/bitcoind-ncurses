#!/usr/bin/env python

##
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
##
from bitcoinrpc.authproxy import AuthServiceProxy
import curses, time, sys, threading, Queue, json, textwrap, ConfigParser

# attrib: user1476056
# https://stackoverflow.com/questions/11303986/addstr-causes-getstr-to-return-on-signal
# re-implement at some point
def getstr(window, prompt = "> ", end_on_error = False):
    result = ""
    starty, startx = window.getyx()
    window.move(starty, 0)
    window.deleteln()
    window.addstr(prompt)
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

def rpc_loop(ncurses_q, json_q):
	config = ConfigParser.ConfigParser()
	config.read('bitcoind-ncurses.conf')
	rpcuser = config.get('rpc', 'rpcuser')
	rpcpassword = config.get('rpc', 'rpcpassword')
	rpcip = config.get('rpc', 'rpcip')
	rpcport = config.get('rpc', 'rpcport')

	rpcurl = "http://" + rpcuser + ":" + rpcpassword + "@" + rpcip + ":" + rpcport
	rpchandle = AuthServiceProxy(rpcurl, None, 500)

	last_blockcount = 0		# ensures block info is updated initially
	last_update = time.time() - 2
	while 1:
		try: s = json_q.get(False)
		except: s = {}
		
		if 'blockheight' in s:
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
			if (cur_blockcount != last_blockcount):		# minimise RPC calls
				#if (last_blockcount == 0):
				lastblocktime = {'lastblocktime': time.time()}
				ncurses_q.put(lastblocktime)
				
				blockhash = rpchandle.getblockhash(cur_blockcount)
				blockinfo = rpchandle.getblock(blockhash)
				ncurses_q.put(blockinfo)
				last_blockcount = cur_blockcount
			
			last_update = time.time()

		time.sleep(0.5)		# minimise RPC calls

def ncurses_loop():
	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()
	curses.curs_set(0)
	
	curses.start_color()
	curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
	
	win = curses.initscr() 
	win.nodelay(1)
	win.keypad(1)

	# random testnet tx
	#s = {'txid': "465b8af08124a1d8fffc6d8320de9d5fa4eb25ba7b0b4f3add5e0f8793c8fc10"}
	#json_q.put(s)

	state = {'mode': "default", 'print_index': 0}

	while 1:
		# die if window too small			
		if (win.getmaxyx()[0] < 10) or (win.getmaxyx()[1] < 75):
			curses.nocbreak()
			curses.endwin()
			sys.stderr.write('Screen size is too small (must be at least 75x10)\n')
			sys.exit(1)

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

			state['block'] = { 'string': [], 'vin': {} } 
			if len(s['hash']) == 64: state['block']['string'].append("block " + state['hash'])
			state['block']['string'].append("height " + str(state['height']) + " size " + str(state['size']))			

			state['block']['string'].append("transactions")			
			state['block']['string'].extend(s['tx'])

		elif 'totalbytesrecv' in s:
			state['totalbytesrecv'] = s['totalbytesrecv']
			state['totalbytessent'] = s['totalbytessent']
		elif 'lastblocktime' in s:
			state['lastblocktime'] = s['lastblocktime']
		elif 'txid' in s:
			state['tx'] = { 'string': [], 'vin': {} } 
			if len(s['txid']) == 64: state['tx']['string'].append("txid " + s['txid'])
			state['tx']['string'].append("")			

			state['tx']['string'].append("inputs")			
			for vin in s['vin']:
				if 'coinbase' in vin: state['tx']['string'].append("coinbase: " + vin['coinbase'])
				elif 'txid' in vin:
					state['tx']['string'].append(vin['txid'] + ":" + "%03u" % vin['vout'])
					state['tx']['vin'][vin['txid']] = vin['vout']
			state['tx']['string'].append("")			

			state['tx']['string'].append("outputs")			
			for vout in s['vout']:
				if 'value' in vout:
					buffer_string = "% 14.8f" % vout['value'] + ": " + vout['scriptPubKey']['asm']
					state['tx']['string'].extend(textwrap.wrap(buffer_string,74)) # change this to scale with window ?

		# draw to screen, default mode
		if state['mode'] == "default":
			win.addstr(0, 1, "bitcoind-ncurses v0.0.2", curses.color_pair(1) + curses.A_BOLD)
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
					if (since_last_block_timestamp > 3600*3):	# assume over 3 hours is syncing
						win.addstr(6, 64, "(syncing)", curses.color_pair(3))
		
			win.addstr(5, 38, "Now (UTC): " + time.asctime(time.gmtime(time.time())))
	
		# draw to screen, transaction view
		elif state['mode'] == "transaction":
		 	if 'tx' in state:
				i = 0
				index = state['print_index']
				offset = 2
				win.clear()
				win.addstr(0, 1, "bitcoind-ncurses - transaction view", curses.color_pair(1) + curses.A_BOLD)
				while i+index < len(state['tx']['string']):
					if (i) < (win.getmaxyx()[0] - 1 - offset):
						win.addstr(i+offset, 1, state['tx']['string'][i+index])
					elif (i) == (win.getmaxyx()[0] - 1 - offset):
						win.addstr(i+offset, 1, "use cursor keys to scroll", curses.A_BOLD + curses.A_REVERSE)
					i += 1
			else:
				win.addstr(0, 1, "no transaction loaded", curses.A_BOLD)
				win.addstr(1, 1, "press 'g' to enter a txid, or 'd' to return to main window", curses.A_BOLD)

		elif state['mode'] == "transaction-input":
			win.clear()
			win.addstr(0, 0, "please type in txid as hex")
			win.refresh()
			textbox = curses.newwin(1,70,1,0) # h,w,y,x
			some_input = getstr(textbox)
			if len(some_input) == 64:
				s = {'txid': some_input}
				json_q.put(s)
			win.clear()
			state['mode'] = "transaction"

		elif state['mode'] == "block":
			if 'block' in state:
				i = 0
				index = state['print_index']
				offset = 2
				win.clear()
				win.addstr(0, 1, "bitcoind-ncurses - block view", curses.color_pair(1) + curses.A_BOLD)
				while i+index < len(state['block']['string']):
					if (i) < (win.getmaxyx()[0] - 1 - offset):
						win.addstr(i+offset, 1, state['block']['string'][i+index])
					elif (i) == (win.getmaxyx()[0] - 1 - offset):
						win.addstr(i+offset, 1, "use cursor keys to scroll", curses.A_BOLD + curses.A_REVERSE)
					i += 1


		win.refresh()

		# take input
		c = win.getch()
		if c == ord('q'):
			break
		if c == ord('d'):
			win.clear()
			state['mode'] = "default"
		if c == ord('t'):
			win.clear()
			state['mode'] = "transaction"
		if c == ord('g'):
			state['mode'] = "transaction-input"
		if c == ord('b'):
			win.clear()
			state['mode'] = "block"
		if c == curses.KEY_DOWN:
			if state['mode'] == "transaction":
				if (state['print_index'] + win.getmaxyx()[0] - 3) < len(state['tx']['string']):
					state['print_index'] += 1
			elif state['mode'] == "block":
				if (state['print_index'] + win.getmaxyx()[0] - 3) < len(state['block']['string']):
					state['print_index'] += 1

		if c == curses.KEY_UP:
			if state['mode'] == "transaction":
				if state['print_index'] > 0: state['print_index'] -= 1
			elif state['mode'] == "block":
				if state['print_index'] > 0: state['print_index'] -= 1

		# delay to avoid excessive CPU usage; todo: base updates on interrupts to avoid needless polling
		time.sleep(0.1)

	# loop was broken, safely quit ncurses	
	curses.nocbreak()
	curses.endwin()
	sys.exit(1) # this appears to abruptly kill the RPC thread

ncurses_q = Queue.Queue()
json_q = Queue.Queue()

thread1 = threading.Thread(target=rpc_loop, args = (ncurses_q, json_q))
thread1.daemon = True
thread1.start()

ncurses_loop()
