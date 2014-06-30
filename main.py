#!/usr/bin/env python

###############################################################################
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
###############################################################################

import threading, Queue, ConfigParser, argparse, signal

import rpc
import interface

def interrupt_signal(signal, frame):
    s = {'stop': 1 }
    rpc_queue.put(s)
    s = {'stop': "Interrupt signal caught"}
    interface_queue.put(s)

def debug(rpc_queue):
    # coinbase testnet transaction for debugging
    #s = {'txid': "cfb8bc436ca1d8b8b2d324a9cb2ef097281d2d8b54ba4239ce447b31b8757df2"}
    # tx with 1001 inputs, 1002 outputs 
    s = {'txid': 'e1dc93e7d1ee2a6a13a9d54183f91a5ae944297724bee53db00a0661badc3005'}
    rpc_queue.put(s)

if __name__ == '__main__':
    # parse commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="path to config file [bitcoind-ncurses.conf]",
                        default="bitcoind-ncurses.conf")
    args = parser.parse_args()

    # parse config file
    config = ConfigParser.ConfigParser()
    config.read(args.config)

    # initialise queues
    interface_queue = Queue.Queue()
    rpc_queue = Queue.Queue()

    # initialise interrupt signal handler (^C)
    signal.signal(signal.SIGINT, interrupt_signal)

    # start RPC thread
    rpc_thread = threading.Thread(target=rpc.loop, args = (interface_queue, rpc_queue, config))
    rpc_thread.daemon = True
    rpc_thread.start()

    #debug(rpc_queue)

    # main loop
    interface.loop(interface_queue, rpc_queue)

    # ensure RPC thread exits cleanly
    rpc_thread.join()
