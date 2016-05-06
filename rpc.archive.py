def actupon(rpchandle, interface_queue, last_update, prev_blockcount, update_interval, s):
    elif 'consolecommand' in s:
        arguments = s['consolecommand'].split()
        command = arguments[0]
        arguments = arguments[1:]

        # TODO: figure out how to encode properly for submission; this is hacky.
        index = 0
        while index < len(arguments):
            if arguments[index].isdigit():
                arguments[index] = int(arguments[index])
            elif arguments[index] == "False":
                arguments[index] = False
            elif arguments[index] == "True":
                arguments[index] = True
            else:
                try:
                    arguments[index] = decimal.Decimal(arguments[index])
                except:
                    pass
            index += 1

        try:
            response = rpcrequest(rpchandle, command, False, *arguments)
            interface_queue.put({'consolecommand': s['consolecommand'], 'consoleresponse': response})
        except:
            interface_queue.put({'consolecommand': s['consolecommand'], 'consoleresponse': "ERROR"})

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
