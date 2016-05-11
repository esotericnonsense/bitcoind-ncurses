import gevent.lock

class Block(object):
    def __init__(self, raw_block):
        assert isinstance(raw_block, dict)
        self.blockhash = raw_block["hash"]
        self.blockheight = raw_block["height"]
        self.chainwork = int(raw_block["chainwork"], 16)
        self.raw_block = raw_block

    def __str__(self):
        return "Block(height={}, hash={})".format(
            self.blockheight, self.blockhash)

class BlockStore(object):
    def __init__(self):
        self._on_block = None # callback on any block
        self._on_best_block = None # callback on block at front of chain

        self._lock = gevent.lock.RLock()
        self._chainwork = 0 # chainwork of best block
        self._blockhashes = {} # height -> blockhash
        self._blocks = {} # hash -> block

    def get_hash(self, blockheight):
        with self._lock:
            return self._blockhashes[blockheight]

    def get_block(self, blockhash):
        with self._lock:
            return self._blocks[blockhash]

    def put_raw_block(self, raw_block):
        block = Block(raw_block)

        with self._lock:
            assert block.blockhash not in self._blocks 
            self._blocks[block.blockhash] = block
            self._blockhashes[block.blockheight] = block.blockhash

            best_block = block.chainwork >= self._chainwork
            if best_block:
                block.chainwork = self._chainwork

        # Callbacks. TODO: should these be async?
        if best_block and self._on_best_block:
            self._on_best_block(block)

        if self._on_block:
            self._on_block(block)

        with open("block.log", "a") as f:
            f.write(str(block) + "\n")
