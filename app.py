from concurrent.futures import thread
from random import choice, randint, random
from dash import Dash, html
import plotly.express as px
import dash_bootstrap_components as dbc
from threading import Thread
from time import sleep

from GUI.callbacks import register_callbacks
from Order.OrderType import OrderType
from Order.OrderAction import OrderAction
from Order.Order import Order
from OrderBook.OrderBook import OrderBook
from Agent.NoiseAgent import NoiseAgent
from GUI.layout import *
from GUI.styles import *

ob = OrderBook()

for _ in range(500):
    a = NoiseAgent(ob.get_id('AGENT'))
    a.update_holdings(round(ob.current_price + random(), 2), randint(1, 100))
    a.update_holdings(round(ob.current_price - random(), 2), randint(1, 100))
    ob.upsert_agent(a)

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'Market Sim'
app.layout = layout(ob)
register_callbacks(app, ob)
    

if __name__ == '__main__':
    app.run(debug=True)
