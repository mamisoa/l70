from pynput import keyboard
import time, sys, termios

break_loop = False
def on_press(key):
    try:
        global break_loop
        # print(f'alpha key {key.char} pressed')
        if key == keyboard.Key.space:
            print('ack sent')
            break_loop = False
        if key == keyboard.Key.esc and break_loop:
            print('esc key pressed, exiting')
            break_loop = True
        print(f'alpha key {key.char} pressed')
        # break_loop = False
    except AttributeError:
        if key == keyboard.Key.esc:
            print('esc key pressed, exiting')
            break_loop = True
        else:
            print(f'special key {key}')
            break_loop = False

def on_release(key):
    print(f'{key} released')
    if key == keyboard.Key.esc:
        return False

listener = keyboard.Listener(
        on_press=on_press)

listener.start()
while True:
    if break_loop == False:
        print('Hello')
        time.sleep(0.5)
    else:
        break

termios.tcflush(sys.stdin, termios.TCIOFLUSH)
