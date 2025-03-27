from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
import time

def setup_matrix():
    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, cascaded=4, block_orientation=90, rotate=0)
    return device

def display_frame(device, frame):
    with canvas(device) as draw:
        for y, row in enumerate(frame):
            for x, pixel in enumerate(row):
                if pixel:
                    draw.point((x, y), fill="white")

smiley = [
    [0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0],
    [0,1,0,0,1,0,0,0,0,0,0,1,0,0,1,0],
    [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],
    [0,1,0,0,1,0,0,0,0,0,0,1,0,0,1,0],
    [0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]

device = setup_matrix()
while True:
    display_frame(device, smiley)
    time.sleep(1)
