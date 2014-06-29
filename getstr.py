#!/usr/bin/env python

# attrib: user1476056
# https://stackoverflow.com/questions/11303986/addstr-causes-getstr-to-return-on-signal
# re-implement at some point
import sys, curses

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

