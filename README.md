# bitcoind-ncurses
ncurses front-end for bitcoind

produced by Amphibian (azeteki, atelopus_zeteki)

## dependencies
* tested with python 2.7.3, bitcoind 0.9.2.0
* jgarzik's bitcoinrpc library (https://github.com/jgarzik/python-bitcoinrpc)

## features
* updating ticker showing bitcoind's status (via RPC)
* facility to view transactions in current block and trace back through their inputs (with -txindex)

## usage
pretty bare bones for now; expect breakage. this will improve over time.

rename example.conf to bitcoind-ncurses.conf and enter your details.

the program will die hard if the config file is incorrect or it fails to connect.

this will be improved in a later release.
 
## launch
```
$ python bitcoind-ncurses.py
$ python bitcoind-ncurses.py -c some_other_config_file.conf
```

## todo
* improve CPU efficiency; change polling method to use interrupts more
* fix tx tree and block tree for high inputs/outputs (scrolling is not implemented)
* wallet and transaction creation support (perhaps in the year 2140)
* bounds checking and so on (paramount for above)

## frog food
found bitcoind-ncurses useful? donations are your way of showing that!

my main machine is currently a 6 year old Atom laptop. upgrading that would be rather useful. cheers!

**1FrogqMmKWtp1AQSyHNbPUm53NnoGBHaBo**
