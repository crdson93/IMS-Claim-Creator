import tkinter as tk
import tkinter.ttk as ttk

# - Function to translate an rgb tuple of int to a tkinter friendly color code - #
def _from_rgb(rgb):
    return '#%02x%02x%02x' % rgb  

jhblue = _from_rgb((26, 54, 104))
header_f = ("Poppins", 16, "bold")  
body_f = ("Poppins", 12)


class Styles:
    def __init__(self):
        self.style = ttk.Style()

#Frame for single agent claim creation
class SingleAgent(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.name_label = ttk.Label(self, text = "Agent Name", font = body_f, style = 'Header.TLabel')
        self.name_entry = ttk.Entry(self, background = jhblue)
        
        self.name_label.pack(side=tk.LEFT)
        self.name_entry.pack(side=tk.LEFT)
        
        self.master.configure(bg = jhblue)

#Frame for new training class claim creation
class TrainingClass(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.label = ttk.Label(self, text = "Training Class")
        self.label.pack()
        self.master.configure(bg = jhblue)

#Frame for new FI claim creation
class NewFI(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.label = ttk.Label(self, text = "NewFI")
        self.label.pack()
        self.master.configure(bg = jhblue)

#Main Window
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("jhCC IMS Claim Creator")

        style = ttk.Style()                     # Creating style element
        style.configure('Option.TCombobox',    # First argument is the name of style. Needs to end with: .TCombobox
            background = jhblue,         # Setting background to our specified color above
            foreground = 'black')         # You can define colors like this also
        
        style.configure('Default.TCombobox',
            background = jhblue,
            foreground = 'grey')
        
        style.configure('Header.TLabel', background = jhblue, foreground = 'white')



        self.title_label = ttk.Label(self, style = 'Header.TLabel', text = "jhCC IMS Claim Creator", font = header_f)

        self.frame1 = SingleAgent(self)
        self.frame2 = TrainingClass(self)
        self.frame3 = NewFI(self)
        self.var = tk.StringVar()
        
        self.dropdown = ttk.Combobox(self, textvariable=self.var, style='Default.TCombobox', values=["Single Agent", "Training Class", "New FI"], font = body_f)
        self.dropdown.set("Please select an option")  # Set the default text here
        self.dropdown.bind("<<ComboboxSelected>>", self.switch_frame)
        
        self.title_label.pack(pady = 6, padx = 6)
        self.dropdown.pack(pady = 6)

    def switch_frame(self, event=None):  # event argument is needed for bind
        frame = self.var.get()
        
        if frame == "Single Agent":
            self.frame2.pack_forget()
            self.frame3.pack_forget()
            self.frame1.pack()
            self.geometry('300x200')
            self.dropdown.configure(style='Option.TCombobox')
        elif frame == "Training Class":
            self.frame1.pack_forget()
            self.frame3.pack_forget()
            self.frame2.pack()
            self.geometry('400x200')
            self.dropdown.configure(style='Option.TCombobox')
        elif frame == "New FI":
            self.frame1.pack_forget()
            self.frame2.pack_forget()
            self.frame3.pack()
            self.geometry('500x200')
            self.dropdown.configure(style='Option.TCombobox')
        else:
            print("Please select a valid option.")
            self.dropdown.set("Please select an option")
            self.dropdown.configure(style='Default.TCombobox')
        

if __name__ == "__main__":
    app = App()
    app.mainloop()
