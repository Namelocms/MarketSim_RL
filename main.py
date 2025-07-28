import tkinter as tk
from App.GUI import OrderBookGUI

if __name__ == '__main__':
    root = tk.Tk()
    app = OrderBookGUI(root, num_agents=10, start_price=1000, maker_cash=1000)
    root.mainloop()