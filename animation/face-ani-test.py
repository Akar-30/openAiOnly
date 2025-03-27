import pygame
import sys

pygame.init()

# LED configuration
LED_SIZE = 20  # size of each LED "pixel"
MARGIN = 2     # gap between LEDs

# Define the face bitmaps (each row is 8 bits)

# Eyes (8x8)
neutral_eye = [
    0b00000000,
    0b00011000,
    0b00111100,
    0b01111110,
    0b01111110,
    0b00111100,
    0b00011000,
    0b00000000
]

spooky_eye = [
    0b00111100,
    0b01111110,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b01111110,
    0b00111100
]

closed_eye_up = [
    0b00000000,
    0b00001100,
    0b00011000,
    0b00011000,
    0b00011000,
    0b00011000,
    0b00001100,
    0b00000000
]

closed_eye_down = [
    0b00000000,
    0b00001100,
    0b00001100,
    0b00000110,
    0b00000110,
    0b00001100,
    0b00001100,
    0b00000000
]

# Mouths (24 rows, broken into three 8-row parts)
happy_mouth = [
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b01100000,
    0b00110000,
    0b00011000,
    0b00001100,
    0b00001110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00001100,
    0b00001100,
    0b00011000,
    0b00110000,
    0b01100000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000
]

sad_mouth = [
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000110,
    0b00001100,
    0b00011000,
    0b00110000,
    0b00110000,
    0b01100000,
    0b01100000,
    0b01100000,
    0b01100000,
    0b01100000,
    0b01100000,
    0b00110000,
    0b00110000,
    0b00011000,
    0b00001100,
    0b00000110,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000
]

very_happy_mouth = [
    0b00000000,
    0b00000000,
    0b01110000,
    0b01111100,
    0b01100110,
    0b01100110,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100011,
    0b01100110,
    0b01100110,
    0b01111100,
    0b01110000,
    0b00000000,
    0b00000000,
    0b00000000
]

neutral_mouth = [
    0b00000000,
    0b00000000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00010000,
    0b00000000,
    0b00000000
]

tongue_mouth = [
    0b00000000,
    0b00000000,
    0b00000100,
    0b11001110,
    0b01111110,
    0b00111110,
    0b00011100,
    0b00001100,
    0b00001110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00000110,
    0b00001100,
    0b00001100,
    0b00011000,
    0b00110000,
    0b01100000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000
]

opened_mouth = [
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00011100,
    0b00100010,
    0b01000001,
    0b01000001,
    0b00100010,
    0b00011100,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000,
    0b00000000
]

# Initial face state
current_left_eye = neutral_eye
current_right_eye = neutral_eye
current_mouth = neutral_mouth

# Dimensions for the displays:
# Eyes: two 8x8 matrices side-by-side (16 columns x 8 rows)
eyes_cols = 16  
eyes_rows = 8

# Mouth: one 8x24 matrix (8 columns x 24 rows)
mouth_cols = 8
mouth_rows = 24

# Calculate display sizes (in pixels)
eyes_width = eyes_cols * (LED_SIZE + MARGIN) + MARGIN
eyes_height = eyes_rows * (LED_SIZE + MARGIN) + MARGIN

mouth_width = mouth_cols * (LED_SIZE + MARGIN) + MARGIN
mouth_height = mouth_rows * (LED_SIZE + MARGIN) + MARGIN

# Window dimensions
window_width = max(eyes_width, mouth_width)
window_height = eyes_height + mouth_height + 20  # additional spacing between eyes and mouth

screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("LED Face Animation Simulation")

def draw_matrix(pattern, rows, cols, top_left):
    """Draw a pattern (list of integers, one per row) as an LED matrix.
       For each row, the leftmost bit corresponds to the first column."""
    x0, y0 = top_left
    for row in range(rows):
        # For safety, if pattern is shorter than expected, use 0.
        value = pattern[row] if row < len(pattern) else 0
        for col in range(cols):
            # Extract bit from MSB to LSB (assuming 8-bit rows)
            bit = (value >> (7 - col)) & 1
            color = (255, 255, 255) if bit else (30, 30, 30)
            x = x0 + MARGIN + col * (LED_SIZE + MARGIN)
            y = y0 + MARGIN + row * (LED_SIZE + MARGIN)
            pygame.draw.rect(screen, color, (x, y, LED_SIZE, LED_SIZE))

def draw_face():
    screen.fill((0, 0, 0))
    # Draw eyes:
    # Left eye: top-left of its own 8x8 display at (0, 0)
    draw_matrix(current_left_eye, 8, 8, (0, 0))
    # Right eye: positioned to the right of left eye.
    draw_matrix(current_right_eye, 8, 8, (8 * (LED_SIZE + MARGIN) + MARGIN, 0))
    # Draw mouth below eyes with a 20-pixel gap.
    draw_matrix(current_mouth, mouth_rows, 8, (0, eyes_height + 20))
    pygame.display.flip()

clock = pygame.time.Clock()

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            key = event.unicode
            # Update eyes based on key input (same mapping as Arduino)
            if key == ':':
                current_left_eye = neutral_eye
                current_right_eye = neutral_eye
            elif key == ';':
                current_left_eye = neutral_eye
                current_right_eye = closed_eye_up
            elif key == '8':
                current_left_eye = spooky_eye
                current_right_eye = spooky_eye
            # Update mouth based on key input
            elif key == ')':
                current_mouth = happy_mouth
            elif key == '(':
                current_mouth = sad_mouth
            elif key in ['D', 'd']:
                current_mouth = very_happy_mouth
            elif key in ['p', 'P']:
                current_mouth = tongue_mouth
            elif key in ['o', 'O']:
                current_mouth = opened_mouth
            elif key == '|':
                current_mouth = neutral_mouth

    draw_face()
    clock.tick(30)
