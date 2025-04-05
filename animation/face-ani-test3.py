import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
FRAME_WIDTH = 64   # assuming each face is 64x64 pixels
FRAME_HEIGHT = 64
COLUMNS = 7        # number of columns in the sprite sheet
ROWS = 7           # number of rows (7x7 = 49 faces)
FPS = 2            # frames per second

# Load the sprite sheet
sprite_sheet = pygame.image.load("face1.png")  # Rename this to your file

# Extract individual frames
def get_face_frames(sheet):
    frames = []
    for row in range(ROWS):
        for col in range(COLUMNS):
            x = col * FRAME_WIDTH
            y = row * FRAME_HEIGHT
            frame = sheet.subsurface((x, y, FRAME_WIDTH, FRAME_HEIGHT))
            frames.append(frame)
    return frames

# Select a subset of face indices for animation (you can change them)
face_sequence = [0, 6, 12, 24, 36, 48]  # Indexes of faces to animate

# Get frames
face_frames = get_face_frames(sprite_sheet)
animation_frames = [face_frames[i] for i in face_sequence]

# Set up display
screen = pygame.display.set_mode((FRAME_WIDTH, FRAME_HEIGHT))
pygame.display.set_caption("Robot Face Animation")
clock = pygame.time.Clock()

# Animation loop
frame_index = 0
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))  # Clear screen
    screen.blit(animation_frames[frame_index], (0, 0))
    frame_index = (frame_index + 1) % len(animation_frames)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()