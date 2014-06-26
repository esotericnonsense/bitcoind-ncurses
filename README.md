# bitcoind-ncurses

ncurses front-end for bitcoind

produced by Amphibian (azeteki, atelopus_zeteki)

## dependencies
* python 2.something
* jgarzik's bitcoinrpc library (https://github.com/jgarzik/python-bitcoinrpc)

## usage
pretty bare bones for now.

rename example.conf to bitcoind-ncurses.conf and enter your details.

the program will die hard if the config file is incorrect or it fails to connect.

this will be improved in a later release.
 
## launch
$ python bitcoind-ncurses.py

## hotkeys
* t: enter transaction view mode
* b: enter block view mode
* d: enter default / stat tracking mode
* up/down arrows: scroll within view modes
* g: enter a txid for viewing
* q: quit bitcoind-ncurses

## todo
* improve CPU efficiency; change polling method to use interrupts more
* add in feature to trace back through a transaction tree
* wallet and transaction creation support?
* bounds checking and so on (paramount for above)

## frog food

found bitcoind-ncurses useful? donations are your way of showing that!

my main machine is currently a 6 year old Atom laptop. upgrading that would be rather useful. cheers!

**1FrogqMmKWtp1AQSyHNbPUm53NnoGBHaBo**
