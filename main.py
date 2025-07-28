import tkinter as tk
from App.GUI import OrderBookGUI
import App.test_integration

if __name__ == '__main__':
    #App.test_integration.test_integration(
    #    num_agents=1000,
    #    maker_agent_cash=100,
    #    maker_agent_volume=100000,
    #    ob_start_price=1.00
    #)
    root = tk.Tk()
    app = OrderBookGUI(root, num_agents=1000, start_price=1, maker_cash=100, maker_volume=10000)
    app.sleep_time = 0.10
    app.after_time = int(app.sleep_time * 1000)
    root.mainloop()