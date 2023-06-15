import tkinter as tk
from tkinter import ttk

def process_selection():
    selection = radio_var.get()
    if selection == 1:
        # do something for option 1
        print("Option 1 selected")
    elif selection == 2:
        # do something for option 2
        print("Option 2 selected")
    else:
        # do something for option 3
        print("Option 3 selected")

root = tk.Tk()

radio_var = tk.IntVar()

radio_button1 = ttk.Radiobutton(root, text="Option 1", variable=radio_var, value=1)
radio_button2 = ttk.Radiobutton(root, text="Option 2", variable=radio_var, value=2)
radio_button3 = ttk.Radiobutton(root, text="Option 3", variable=radio_var, value=3)

radio_button1.pack()
radio_button2.pack()
radio_button3.pack()

process_button = ttk.Button(root, text="Process", command=process_selection)
process_button.pack()

root.mainloop()

