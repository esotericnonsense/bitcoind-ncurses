# bitcoind-ncurses v0.0.23

Python ncurses front-end for bitcoind. Uses the JSON-RPC API.

![ScreenShot](/screenshots/bitcoind-ncurses.gif)

- azeteki (Atelopus Zeteki)

## Dependencies

* Developed with python 2.7, Bitcoin Core 0.9.4
* jgarzik's python-bitcoinrpc library (https://github.com/jgarzik/python-bitcoinrpc)
* (Windows only) Python ncurses library (http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses)

## Features

* Updating ticker showing bitcoind's status
* Basic block explorer with fast seeking and no external database required
* View transactions in blocks, trace back through their inputs and display scripts (best with -txindex)
* View wallet transactions (txid, transaction value, cumulative balance)
* View connected peers and chain tips
* Network bandwidth monitor
* Basic debug console functionality (WARNING: do not use for transactions)

## Installation

```
git clone https://github.com/azeteki/bitcoind-ncurses
git clone https://github.com/jgarzik/python-bitcoinrpc
mv python-bitcoinrpc/bitcoinrpc bitcoind-ncurses/
```

Copy ~/.bitcoin/bitcoin.conf to bitcoind-ncurses's folder, or alternatively run with the switch --config=/path/to/bitcoin.conf

This is an early development release. Expect the unexpected.

## Launch

Note that bitcoind-ncurses requires Python 2 due to the bitcoinrpc dependency.

```
$ python main.py
$ python2 main.py
```

Frog Food
---------

If you have found bitcoind-ncurses useful, please consider donating.
The funds will be used for creating future Bitcoin development projects.

![ScreenShot](/screenshots/donation-qr.png)

**1FrogqMmKWtp1AQSyHNbPUm53NnoGBHaBo**
