import tkinter as tk
from App.GUI import OrderBookGUI

if __name__ == '__main__':
    root = tk.Tk()
    app = OrderBookGUI(root)
    root.mainloop()