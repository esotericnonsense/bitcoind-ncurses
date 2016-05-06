elif 'findblockbytimestamp' in s:
    request = s['findblockbytimestamp']

    # initializing the while loop
    block_to_try = 0
    delta = 10000
    iterations = 0

    while abs(delta) > 3600 and iterations < 15: # one day
        block = getblock(rpchandle, interface_queue, block_to_try, True)
        if not block:
            break

        delta = request - block['time']
        block_to_try += int(delta / 600) # guess 10 mins per block. seems to work on testnet anyway

        if (block_to_try < 0):
            block = getblock(rpchandle, interface_queue, 0, True)
            break # assume genesis has earliest timestamp

        elif (block_to_try > blockcount):
            block = getblock(rpchandle, interface_queue, blockcount, True)
            break

        iterations += 1
