import tkinter as tk
from tkinter import ttk
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from random import randint

from OrderBook.OrderBook import OrderBook
from Agent.NoiseAgent import NoiseAgent


class OrderBookGUI:
    def __init__(self, root, num_agents=100, start_price=1.00, maker_volume=19900000, maker_cash=1000):
        self.root = root
        self.root.title("Order Book GUI")
        self.sleep_time = 0.5
        self.after_time = int(self.sleep_time * 1000)
        self.num_agents = num_agents

        # Initialize OrderBook
        self.ob = OrderBook()
        self.ob.current_price = start_price
        self.prices = []

        # Setup agents
        self.init_agents(num_agents=self.num_agents, maker_cash=maker_cash, maker_volume=maker_volume)

        # Tabs
        self.tab_control = ttk.Notebook(root)
        self.tab_chart = tk.Frame(self.tab_control, bg='#2e2e2e')
        self.tab_agents = tk.Frame(self.tab_control, bg='#2e2e2e')


        self.tab_control.add(self.tab_chart, text='Price Chart')
        self.tab_control.add(self.tab_agents, text='Agents')
        self.tab_control.pack(expand=1, fill='both')

        self.setup_dark_theme()
        self.setup_chart()
        self.setup_agents_tab()

        # Start the simulation in another thread
        self.running = True
        threading.Thread(target=self.run_simulation, daemon=True).start()
        self.update_gui()

    def setup_dark_theme(self):
        style = ttk.Style()
        style.theme_use('default')

        # Set dark backgrounds and light text for general widgets
        style.configure('.', background='#2e2e2e', foreground='white', fieldbackground='#2e2e2e')

        # Treeview customization
        style.configure('Treeview',
            background='#1e1e1e',
            foreground='white',
            rowheight=25,
            fieldbackground='#1e1e1e'
        )
        style.map('Treeview',
            background=[('selected', '#444444')],
            foreground=[('selected', 'white')]
        )

        self.root.configure(bg='#2e2e2e')
        self.tab_chart.configure(bg='#2e2e2e')
        self.tab_agents.configure(bg='#2e2e2e')


    def init_agents(self, num_agents, maker_cash, maker_volume):
        self.maker = NoiseAgent('MAKER', cash=maker_cash)
        self.maker.update_holdings(self.ob.current_price, maker_volume)
        self.ob.upsert_agent(self.maker)
        for _ in range(num_agents):
            agent = NoiseAgent(self.ob.get_id('AGENT'), randint(10, 1000))
            self.ob.upsert_agent(agent)

    def setup_chart(self):
        # Frame for the chart
        chart_frame = tk.Frame(self.tab_chart)
        chart_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frame for the order book tables (below the chart)
        ob_frame = tk.Frame(self.tab_chart)
        ob_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Ask Table
        self.ask_tree = ttk.Treeview(ob_frame, columns=('Price', 'Volume'), show='headings', height=8)
        self.ask_tree.heading('Price', text='Ask Price')
        self.ask_tree.heading('Volume', text='Volume')
        self.ask_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bid Table
        self.bid_tree = ttk.Treeview(ob_frame, columns=('Price', 'Volume'), show='headings', height=8)
        self.bid_tree.heading('Price', text='Bid Price')
        self.bid_tree.heading('Volume', text='Volume')
        self.bid_tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


    def setup_agents_tab(self):
        self.agent_tree = ttk.Treeview(
            self.tab_agents,
            columns=('ID', 'Cash', 'Holdings', 'Total Shares'),
            show='headings'
        )
        self.agent_tree.heading('ID', text='ID')
        self.agent_tree.heading('Cash', text='Cash')
        self.agent_tree.heading('Holdings', text='Holdings')
        self.agent_tree.heading('Total Shares', text='Total Shares')
        self.agent_tree.pack(fill=tk.BOTH, expand=True)

    def run_simulation(self):
        while self.running:
            for agent in self.ob.agents.values():
                agent.act(self.ob)
            self.prices.append(self.ob.current_price)
            time.sleep(self.sleep_time)

    def update_gui(self):
        # Update chart
        self.ax.clear()
        self.ax.set_facecolor('#1e1e1e')
        self.fig.patch.set_facecolor('#2e2e2e')
        self.ax.plot(self.prices[-100:], label='Price', color='cyan')
        self.ax.set_title("Order Book Price", color='white')
        self.ax.set_ylabel("Price", color='white')
        self.ax.tick_params(colors='white')
        self.ax.legend(facecolor='#1e1e1e', edgecolor='white')
        self.canvas.draw()


        for i in self.agent_tree.get_children():
            self.agent_tree.delete(i)
        for agent in self.ob.agents.values():
            holdings_str = ', '.join([f'{round(p, 2)}: {v}' for p, v in agent.holdings.items()])
            self.agent_tree.insert('', tk.END, values=(
                agent.id,
                round(agent.cash, 2),
                holdings_str,
                agent.get_total_shares()
            ))

        # Update order book using snapshot
        for tree in (self.ask_tree, self.bid_tree):
            for i in tree.get_children():
                tree.delete(i)

        snapshot = self.ob.get_snapshot(depth=10)[0]
        for ask in snapshot['asks']:
            self.ask_tree.insert('', tk.END, values=(round(ask['price'], 4), ask['size']))
        for bid in snapshot['bids']:
            self.bid_tree.insert('', tk.END, values=(round(bid['price'], 4), bid['size']))


        self.root.after(self.after_time, self.update_gui)
