from tkinter import *
from tkinter import ttk

def main():
    # print("Welcome to the new app!")

    root = Tk()
    root.title("Finances App")

    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(mainframe, text="Welcome to the Finances App!").grid(column=1, row=1, sticky=W)
    ttk.Button(mainframe, text="Quit", command=root.destroy).grid(column=1, row=2, sticky=W)
    ttk.Button(mainframe, text="Test Button", command=lambda: print("Test Button Clicked")).grid(column=2, row=2, sticky=W)

    root.mainloop()

if __name__ == "__main__":
    main()