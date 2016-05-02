#!/usr/bin/env python

###############################################################################
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# wumpus and kylemanna for configuration file parsing
# all the users for their suggestions and testing
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
###############################################################################

from gevent import monkey
monkey.patch_all()
import gevent
import gevent.queue

import argparse, signal

import rpc
import interface
import config

def interrupt_signal(signal, frame):
    s = {'stop': "Interrupt signal caught"}
    interface_queue.put(s)

if __name__ == '__main__':
    # initialise queues
    interface_queue = gevent.queue.Queue()
    rpc_queue = gevent.queue.Queue()

    # parse commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="path to config file [bitcoin.conf]",
                        default="bitcoin.conf")
    args = parser.parse_args()

    # parse config file
    try:
        cfg = config.read_file(args.config)
    except IOError:
        cfg = {}
        s = {'stop': "configuration file [" + args.config + "] does not exist or could not be read"}
        interface_queue.put(s)

    # initialise interrupt signal handler (^C)
    signal.signal(signal.SIGINT, interrupt_signal)

    # start RPC thread
    rpc_process = gevent.spawn(rpc.loop, interface_queue, rpc_queue, cfg)

    # main loop
    interface.main(interface_queue, rpc_queue)

    # ensure RPC thread exits cleanly
    rpc_process.join()
