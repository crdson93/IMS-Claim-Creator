import tkinter as tk
from tkinter import ttk

def process_selection():
    option_1 = option_1_var.get()
    option_2 = option_2_var.get()
    option_3 = option_3_var.get()

    if option_1:
        # do something for option 1
        print("Option 1 selected")
    if option_2:
        # do something for option 2
        print("Option 2 selected")
    if option_3:
        # do something for option 3
        print("Option 3 selected")

root = tk.Tk()

option_1_var = tk.BooleanVar()
option_2_var = tk.BooleanVar()
option_3_var = tk.BooleanVar()

check_button1 = ttk.Checkbutton(root, text="Option 1", variable=option_1_var)
check_button2 = ttk.Checkbutton(root, text="Option 2", variable=option_2_var)
check_button3 = ttk.Checkbutton(root, text="Option 3", variable=option_3_var)

check_button1.pack()
check_button2.pack()
check_button3.pack()

process_button = ttk.Button(root, text="Process", command=process_selection)
process_button.pack()

root.mainloop()

