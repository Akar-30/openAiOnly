import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Funny Robot Face")

# Set the canvas size and background color
canvas = tk.Canvas(root, width=660, height=660, bg="black")
canvas.pack()

# Coordinates for eyes and mouth
eye_left = (176, 220, 264, 308)
eye_right = (396, 220, 484, 308)
mouth_base = (264, 396, 396, 440)  # Base mouth coordinates
mouth_height_variation = [440, 442, 444, 446, 448, 450, 452, 454, 456, 458, 460, 458, 456, 454, 452, 450, 448, 446, 444, 442, 440]  # Smoother animation sequence

# Draw the eyes
canvas.create_oval(eye_left, fill="white", outline="")
canvas.create_oval(eye_right, fill="white", outline="")

# Draw the grid lines on eyes to recreate the mesh effect
for i in range(176, 265, 9):
    canvas.create_line(i, 220, i, 308, fill='black')
for j in range(220, 309, 9):
    canvas.create_line(176, j, 264, j, fill='black')

for i in range(396, 485, 9):
    canvas.create_line(i, 220, i, 308, fill='black')
for j in range(220, 309, 9):
    canvas.create_line(396, j, 484, j, fill='black')

# Function to animate the mouth
mouth_index = 0  # Index to track the current mouth height

def animate_mouth():
    global mouth_index
    # Clear the previous mouth
    canvas.delete("mouth")

    # Update the mouth height
    current_mouth = (264, 396, 396, mouth_height_variation[mouth_index])
    canvas.create_arc(current_mouth, start=180, extent=180, style='chord', fill='white', outline='', tags="mouth")

    # Update the grid lines for the mouth
    for i in range(264, 397, 9):
        canvas.create_line(i, 396, i, mouth_height_variation[mouth_index], fill='black', tags="mouth")
    for j in range(396, mouth_height_variation[mouth_index] + 1, 6):
        canvas.create_line(264, j, 396, j, fill='black', tags="mouth")

    # Update the index for the next frame
    mouth_index = (mouth_index + 1) % len(mouth_height_variation)

    # Schedule the next frame
    root.after(50, animate_mouth)  # Reduced delay for smoother animation

# Start the animation
animate_mouth()

root.mainloop()