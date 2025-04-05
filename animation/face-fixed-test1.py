import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Funny Robot Face")

# Set the canvas size and background color (increased resolution by 10%)
canvas = tk.Canvas(root, width=660, height=660, bg="black")
canvas.pack()

# Coordinates for eyes and mouth (scaled for higher resolution by 10%)
eye_left = (176, 220, 264, 308)
eye_right = (396, 220, 484, 308)
mouth = (264, 396, 396, 440)  # Increased height for the mouth

# Draw the eyes
canvas.create_oval(eye_left, fill="white", outline="")
canvas.create_oval(eye_right, fill="white", outline="")

# Draw the grid lines on eyes to recreate the mesh effect (finer grid for higher resolution)
for i in range(176, 265, 9):  # Adjusted step size for finer grid
    canvas.create_line(i, 220, i, 308, fill='black')
for j in range(220, 309, 9):
    canvas.create_line(176, j, 264, j, fill='black')

for i in range(396, 485, 9):
    canvas.create_line(i, 220, i, 308, fill='black')
for j in range(220, 309, 9):
    canvas.create_line(396, j, 484, j, fill='black')

# Draw the smiling mouth
canvas.create_arc(mouth, start=180, extent=180, style='chord', fill='white', outline='')

# Draw mouth grid lines (mesh effect, finer grid)
for i in range(264, 397, 9):
    canvas.create_line(i, 396, i, 440, fill='black')
for j in range(396, 441, 6):  # Adjusted step size for finer grid
    canvas.create_line(264, j, 396, j, fill='black')

root.mainloop()