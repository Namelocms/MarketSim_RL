import tkinter as tk
from App.GUI import OrderBookGUI
import App.test_integration


if __name__ == '__main__':
    #App.test_integration.test_integration(
    #    num_agents=10,
    #    maker_agent_cash=100,
    #    maker_agent_volume=1000,
    #    ob_start_price=0.10
    #)
    root = tk.Tk()
    app = OrderBookGUI(
        root, 
        num_agents=225, 
        agent_cash=10.00, 
        start_price=0.225506, 
        maker_cash=0, 
        maker_volume=10000
    )
    app.sleep_time = 0.10  # 10 iterations per second, 1 every 100ms
    app.after_time = int(app.sleep_time * 1000)
    root.mainloop()