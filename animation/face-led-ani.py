import time
from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
import threading

# LED Matrix Configuration
options = RGBMatrixOptions()
options.rows = 32         # Change to 16 or 32 based on your matrix
options.cols = 64         # change to 32 or 64 based on your matrix
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular'  # Adapt based on your configuration
matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

# Define colors
white = graphics.Color(255, 255, 255)
black = graphics.Color(0, 0, 0)

# COMMON UTILITY FUNCTIONS
def clear_canvas():
    canvas.Clear()

def draw_pixel(x, y, color=white):
    canvas.SetPixel(x, y, color.red, color.green, color.blue)

# FACE GRAPHICS FUNCTIONS
def draw_eyes(open=True, crossed=False, wide=False, tilted=False, closed=False):
    # Eye positions
    left_x, right_x = 15, 48
    eye_y = 10

    size = 2 if wide else 1

    if closed:
        for x in range(-size-1, size+2):
            draw_pixel(left_x + x, eye_y)
            draw_pixel(right_x + x, eye_y)
        return

    if crossed:
        # X eyes for error status
        offsets = [(-2,-2),(-1,-1),(0,0),(1,1),(2,2),(-2,2),(-1,1),(1,-1),(2,-2)]
        for d in offsets:
            lx = left_x + d[0]
            ly = eye_y + d[1]
            rx = right_x + d[0]
            ry = eye_y + d[1]
            draw_pixel(lx, ly)
            draw_pixel(rx, ry)
        return

    # Regular eyes
    y_offset = -1 if tilted else 0
    for dx in range(-size, size+1):
        for dy in range(-size, size+1):
            draw_pixel(left_x + dx, eye_y + dy + y_offset)
            draw_pixel(right_x + dx, eye_y + dy - y_offset)

def draw_mouth(type='neutral', offset=0):
    mouth_x, mouth_y = 32, 22 + offset

    if type == 'neutral':
        # Simple straight line
        for x in range(-5, 6):
            draw_pixel(mouth_x + x, mouth_y)
    elif type == 'happy':
        coords = [(-4,0), (-3,1), (-2,2), (-1,2), (0,2), (1,2), (2,2), (3,1), (4,0)]
        for x,y in coords:
            draw_pixel(mouth_x+x, mouth_y+y)
    elif type == 'speaking':
        coords = [(-3,0), (-2,1), (-1,1), (0,1), (1,1), (2,1), (3,0),
                  (-3,0), (-2,-1), (-1,-1), (0,-1), (1,-1), (2,-1), (3,0)]
        for x,y in coords:
            draw_pixel(mouth_x+x,mouth_y+y)
    elif type == 'zigzag':
        coords = [(-3,0),(-2,-1),(-1,0),(0,-1),(1,0),(2,-1),(3,0)]
        for x,y in coords:
            draw_pixel(mouth_x+x,mouth_y+y)
    elif type == 'thinking':
        # neutral mouth for thinking, dots will appear above externally
        for x in range(-3,4):
            draw_pixel(mouth_x+x,mouth_y)
    elif type == 'sleep':
        coords = [(-3,0),(-2,-1),(-1,-1),(0,-1),(1,-1),(2,-1),(3,0)]
        for x,y in coords:
            draw_pixel(mouth_x+x,mouth_y+y)

def draw_z(x,y):
    coords = [(-1,-1),(0,-1),(1,-1),(0,0),(-1,1),(0,1),(1,1)]
    for dx,dy in coords:
        draw_pixel(x+dx,y+dy)

# ANIMATIONS
def animate_speaking(duration=5):
    end_time = time.time() + duration
    while time.time() < end_time:
        clear_canvas()
        draw_eyes(open=True)
        draw_mouth(type='speaking', offset=-1)
        matrix.SwapOnVSync(canvas)
        time.sleep(0.2)

        clear_canvas()
        draw_eyes(open=True)
        draw_mouth(type='speaking', offset=1)
        matrix.SwapOnVSync(canvas)
        time.sleep(0.2)

def animate_listening(duration=5):
    end_time = time.time() + duration
    wave_pos = 5
    direction = 1
    while time.time() < end_time:
        clear_canvas()
        draw_eyes(open=True, wide=True)
        draw_mouth(type='neutral')
        draw_pixel(wave_pos, 15)  # Animated listening indicator
        matrix.SwapOnVSync(canvas)

        wave_pos += direction
        if wave_pos <= 4 or wave_pos >= 60:
            direction *= -1
        time.sleep(0.1)

def animate_thinking(duration=5):
    end_time = time.time() + duration
    dots = [28,32,36]
    while time.time() < end_time:
        clear_canvas()
        draw_eyes(tilted=True)
        draw_mouth(type='thinking')
        for dot in dots:
            draw_pixel(dot,19)
        matrix.SwapOnVSync(canvas)
        dots = [(dot+1) if dot<36 else 28 for dot in dots]
        time.sleep(0.2)

def animate_error(duration=5):
    end_time = time.time() + duration
    while time.time() < end_time:
        clear_canvas()
        draw_eyes(crossed=True)
        draw_mouth(type='zigzag')
        matrix.SwapOnVSync(canvas)
        time.sleep(0.5)

def animate_happy(duration=5):
    end_time = time.time() + duration
    while time.time() < end_time:
        clear_canvas()
        draw_eyes(open=True)
        draw_mouth(type='happy')
        matrix.SwapOnVSync(canvas)
        time.sleep(0.8)

        # Blink Effect
        clear_canvas()
        draw_eyes(closed=True)
        draw_mouth(type='happy')
        matrix.SwapOnVSync(canvas)
        time.sleep(0.2)

def animate_sleep(duration=5):
    end_time = time.time() + duration
    z_pos = 12
    while time.time() < end_time:
        clear_canvas()
        draw_eyes(closed=True)
        draw_mouth(type='sleep')
        draw_z(z_pos,4)
        matrix.SwapOnVSync(canvas)

        z_pos += 1
        if z_pos > 50:
            z_pos = 12
        time.sleep(0.3)

# MAIN CONTROL LOOP
animation_functions = [
    animate_speaking,
    animate_listening,
    animate_thinking,
    animate_error,
    animate_happy,
    animate_sleep
]

def main_loop():
    try:
        while True:
            for anim in animation_functions:
                anim(duration=5)
    except KeyboardInterrupt:
        clear_canvas()
        matrix.SwapOnVSync(canvas)

if __name__ == "__main__":
    print("Starting facial animations. Press Ctrl+C to exit.")
    main_loop()