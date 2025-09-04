from dash import html, dcc
import dash_bootstrap_components as dbc
from plotly.express import line
from pandas import DataFrame

from GUI.styles import *
from Order.OrderAction import OrderAction
from OrderBook.OrderBook import OrderBook

UI_REFRESH_SEC = 1

def order_card_content(price, volume):
    return dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col([html.P(price, className='order-price-p'),]),
                    dbc.Col([html.P(volume, className='order-volume-p'),])
                    
                ],
                justify='between',
                class_name='order-card-content'
            ),
        ],
        
    )

def order_card(price, volume, side: OrderAction, is_best = False):
    match side:
        case OrderAction.ASK:
            color = 'danger'
            _className = 'order-card-ask'
        case OrderAction.BID:
            color = 'success'
            _className = 'order-card-bid'
        case _:
            color = 'secondary'
            _className = 'order-card-other'
    return dbc.Card(
        [
            order_card_content(price, volume)
        ],
        color=color,
        outline=not is_best,
        inverse=is_best,
        class_name=_className
    )

def tile(type, style: dict = {}):
    return dbc.Container(
        children=[],
        id=f'tile-{type}',
        className='tile custom-scrollbar',
        style=style
    )

def order_col():
    return dbc.Col(
        [
            tile('asks', {'height': '100%', 'flexDirection': 'column-reverse'}),
            tile('bids', {'height': '100%'}),
        ],
        class_name='order-col',
        width=3
    )

def actions_row():
    actions_ask = tile('actions-ask')
    actions_bid = tile('actions-bid')

    actions_ask.children = [
        html.P('ASK ACTIONS')
    ]
    actions_bid.children = [
        html.P('BID ACTIONS')
    ]

    return dbc.Row(
        [
            actions_ask,
            actions_bid
        ],
        class_name='actions-row',
    )

def graph_col():
    fig = dict({
        'data': [{
            'type': 'line',
            'x': [],
            'y': [],
        }],
        'layout': {'title': {'text': 'MarketSim Price Track'}}
    })
    graph_tile = tile('graph')
    graph_tile.children = [
        dcc.Graph(id='graph', figure=fig, className='graph-fig'),
    ]
    return dbc.Col(
        [
            graph_tile,
            tile('ob-info', {'flexDirection': 'row', 'width': '100%'}),
            actions_row(),
        ],
        class_name='graph-col',
        width=6
    )

def agent_col(ob: OrderBook):
    agents = tile('agents', {'height': '100%'})
    agents.children = [
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    [],
                    title=a_id,
                    id={'type': 'acc-item', 'index': a_id},
                )
                for a_id, agent in list(ob.agents.items())
            ],
            class_name='agent-accordian custom-scrollbar',
            id='agent-accordian',
            start_collapsed=True,
        )
    ]
    return dbc.Col(
        [
            agents,
        ],
        class_name='agent-col',
        width=3,
    )

def layout(ob: OrderBook):
    return dbc.Container(
        [
            dbc.Row(
                [
                    order_col(),
                    graph_col(),
                    agent_col(ob),
                ],
                class_name='main-row',
            ),
            dcc.Interval(
                id='ui-interval',
                interval=UI_REFRESH_SEC * 1000,
                n_intervals=0
            ),
            html.Div([], id='hidden-div')
        ],
        class_name='main-container',
    )