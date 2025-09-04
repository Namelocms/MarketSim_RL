from dash import ALL, MATCH, Dash, callback, Input, Output, State, html, dcc, ctx
import datetime
from pandas import DataFrame
from plotly.express import line
import dash_bootstrap_components as dbc

from Agent.Agent import Agent
from GUI.layout import order_card
from Order.OrderAction import OrderAction
from OrderBook.OrderBook import OrderBook
from Util.Util import Util

prices = []
times = []

def register_callbacks(app: Dash, ob: OrderBook):

    @app.callback(
        Output('hidden-div', 'children'),
        Input('ui-interval', 'n_intervals'),
    )
    def update_sim(_):
        agents = list(ob.agents.values())
        for agent in agents:
            agent.act(ob)
        return None

    @app.callback(
        Output('tile-asks', 'children'),
        Output('tile-bids', 'children'),
        Output('graph', 'figure'),
        Output('tile-ob-info', 'children'),
        Input('ui-interval', 'n_intervals')
    )
    def update_ui(_):

        data = ob.get_snapshot(50)[0]
        asks = data['asks']
        bids = data['bids']
        ask_cards = []
        bid_cards = []

        i = 0
        if len(asks) > 0:
            for order in asks:
                ask_cards.append(order_card(order['price'], order['size'], OrderAction.ASK, is_best=True if i == 0 else False))
                i += 1
        else:
            ask_cards.append(order_card('N/A', 'ASKS', None))
        if len(bids) > 0:
            j = 0
            for order in bids:
                bid_cards.append(order_card(order['price'], order['size'], OrderAction.BID, is_best=True if j == 0 else False))
                j += 1
        else:
            bid_cards.append(order_card('N/A', 'BIDS', None))

        current_price = ob.current_price
        best_ask = ob.get_best(OrderAction.ASK)
        best_bid = ob.get_best(OrderAction.BID)
        spread = round(best_ask[0] - best_bid[0], Util.ROUND_NDIGITS) if best_ask != () and best_bid != () else 'N/A'

        prices.append(current_price)
        times.append(datetime.datetime.now().time())

        ob_info = [
            order_card(min(prices), 'Low', None), 
            order_card(current_price, 'Current', None), 
            order_card(max(prices), 'High', None),
            order_card(spread, 'Spread', None)
        ]
        
        fig = dict({
            'data': [{
                'type': 'line',
                'x': times[-20:],
                'y': prices[-20:],
            }],
            'layout': {'title': {'text': 'MarketSim Price Track'}}
        })
        
        return ask_cards, bid_cards, fig, ob_info

    @app.callback(
        Output({'type': 'acc-item', 'index': ALL}, 'children'),
        [Input('agent-accordian', 'active-item')],
        prevent_initial_call=True,
    )
    def get_agent_info(item):
        agent: Agent = ob.get_agent_by_id(ctx.triggered_id['index'])

        holding_rows = []
        for price, volume in list(agent.holdings.items()):
            holding_rows.append(html.Tr([html.Td(f'${price}'), html.Td(volume)]))
        holding_table_header = [html.Thead(html.Tr(
            [
                html.Th('Price'), 
                html.Th('Volume'),
            ]
        ))]
        holding_table_body = [html.Tbody(holding_rows)]
        holding_table = dbc.Table(holding_table_header + holding_table_body, bordered=True)

        active_orders_rows = []
        for order in agent.active_asks.values():
            active_orders_rows.append(html.Tr(
                [
                    html.Td(f'${order.side}'), 
                    html.Td(order.type), 
                    html.Td(order.price),
                    html.Td(order.volume),
                    html.Td(order.entry_volume),
                    html.Td(order.status),
                    html.Td(order.timestamp),
                ]))
        for order in agent.active_bids.values():
            active_orders_rows.append(html.Tr(
                [
                    html.Td(f'${order.side}'), 
                    html.Td(order.type), 
                    html.Td(order.price),
                    html.Td(order.volume),
                    html.Td(order.entry_volume),
                    html.Td(order.status),
                    html.Td(order.timestamp),
                ]))
        active_orders_table_header = [html.Thead(html.Tr(
            [
                html.Th('Side'), 
                html.Th('Type'),
                html.Th('Price'),
                html.Th('Volume'),
                html.Th('Entry Volume'),
                html.Th('Status'),
                html.Th('Timestamp'),
            ]
        ))]
        active_orders_table_body = [html.Tbody(active_orders_rows)]
        active_orders_table = dbc.Table(active_orders_table_header + active_orders_table_body, border=True)

        acc_item_children = [
            html.P(agent.cash),
            html.P(agent.get_total_shares()),
            dbc.Button(
                'Holdings',
                id="holdings-collapse-button",
                className="mb-3",
                color="primary",
                n_clicks=0,
            ),
            dbc.Collapse(
                dbc.Card(dbc.CardBody([holding_table])),
                id="holdings-collapse",
                is_open=False,
            ),
            dbc.Button(
                'Active Orders',
                id="active-orders-collapse-button",
                className="mb-3",
                color="primary",
                n_clicks=0,
            ),
            dbc.Collapse(
                dbc.Card(dbc.CardBody([active_orders_table])),
                id="active-orders-collapse",
                is_open=False,
            ),
        ]
        return acc_item_children

    @app.callback(
        Output("holdings-collapse", "is_open"),
        [Input("holdings-collapse-button", "n_clicks")],
        [State("holdings-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_collapse(n, is_open):
        return not is_open

    @app.callback(
        Output("active-orders-collapse", "is_open"),
        [Input("active-orders-collapse-button", "n_clicks")],
        [State("active-orders-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_collapse(n, is_open):
        return not is_open