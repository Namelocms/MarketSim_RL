import numpy as np
from numpy.random import pareto
import matplotlib.pyplot as plt
from scipy.stats import beta, truncnorm
from math import pi, sin, log10

def generate_price(current_price, volatility=0.01, drift=0.01):
    ''' Generates a normal distribution with a drift% away from the current price then clips anything outside acceptable range back to current price
        Dosen't really work since the clipping causes unnatural biases right next to the current price
    '''
    log_return = np.random.normal(loc=drift, scale=volatility)
    price = current_price * np.exp(log_return)
    if drift < 0:
        price = np.clip(price, 0, current_price)
    else:
        price = np.clip(price, current_price, 1000000)
    return price    

def exponential_price(current_price, side, A=0.05, lam=5):
    ''' Creates a nonlinear decay away from the price, with most orders close, and some far
        Spread is too big on the tails, could try limiting to within a certain amount?
    '''
    match side:
        case 'BID':
            x = np.random.rand()
            offset = A * (1 - np.exp(lam * x))
            return current_price * (1 + offset)
        case 'ASK':
            x = np.random.rand()
            offset = A * (1 - np.exp(lam * x))
            return current_price * (1 - offset)

def pareto_price(current_price, side, shape=5, scale=0.01):
    ''' Never touch the current price and offer "fat-tailed" randomness, great for rare aggressive orders
        Seems pretty good, spread works well for low price but seems to be a little exagerated at high price, could be adjusted with scale/shape (shape 5 seems pretty good)
    '''
    match side:
        case 'BID':
            offset = pareto(shape) * scale
            return current_price / (1 + offset)
        case 'ASK':
            offset = pareto(shape) * scale  # scale adjusts closeness
            return current_price * (1 + offset)

#######################################################################################################
def get_max_variance(price, scale=0.1, decay_rate=0.25, amplitude=0.1, frequency=pi*2):
    '''
    Get the max variance in price (how much the computed price will differ from passed price)

    scale = Scale factor, controls the overall height of the curve\n
    decay_rate = The power-law decay rate, larger decay_rate -> variance falls off faster as price increases\n
    amplitude = The sinusoidal amplitude, controls how much the variance "wiggles" above/below the base curve. Set to 0 to disable sine behavior\n
    frequency = The frequency of the sine (in log space), higher frequency -> more wiggles per log unit of price\n

    PRICE__||  max_variance\n
    0.1____||  0.17783\n
    1______||  0.10000\n
    10_____||  0.05623\n
    100____||  0.03162\n
    1000___||  0.01778\n
    10000__||  0.01000\n
    100000_||  0.00562
    '''
    return scale * (price ** -decay_rate) * (1 + (amplitude * sin(frequency * log10(price))))


def beta_price(current_price, side, a=2, b=5):
    ''' Can be shaped to hug the current price without reaching it: [a > b: hugs lower end || a < b: hugs upper end]
        Has a nice distribution just a little past/before the current price is where most orders will be placed
    '''
    max_variance = get_max_variance(
            current_price,
            scale=0.05,
            decay_rate=0.25,
            amplitude=0.1,
            frequency=pi*2
        )
    epsilon = 0.000001  # Min possible price
    match side:
        case 'BID':
            x = beta.rvs(a, b)
            discount = x * max_variance
            return max(current_price * (1 - discount), epsilon)
        case 'ASK':
            x = beta.rvs(a, b)
            premium = x * max_variance
            return current_price * (1 + premium)


#######################################################################################################

def soft_limit_buy_price(current_price, side, alpha=0.02, steepness=7):
    ''' This lets you model orders clustering closer or farther from the current price depending on steepness
        Really hugs the current price but has an offset from it with lower steepness that excludes important prices and then its too close with higher steepness
    '''
    match side:
        case 'BID':
            x = np.random.rand()
            offset = alpha / (1 + np.exp(steepness * x))
            return current_price * (1 - offset)
        case 'ASK':
            x = np.random.rand()
            offset = alpha / (1 + np.exp(steepness * x))
            return current_price * (1 + offset)


def log_uniform_price(current_price, side, min_pct=0.001, max_pct=0.05):
    ''' Uniform in log-space (like exponential, but symmetric in log terms), giving "even spread" in % change.
        Spread is too even and the offset from the current price causes prices to be lost
    '''
    match side:
        case 'BID':
            low = np.log(1 - max_pct)
            high = np.log(1 - min_pct)
            offset = np.exp(np.random.uniform(low, high))
            return current_price * offset
        case 'ASK':
            low = np.log(1 + min_pct)
            high = np.log(1 + max_pct)
            offset = np.exp(np.random.uniform(low, high))
            return current_price * offset

 
def truncated_price(current_price, side, volatility=0.001):
    ''' This gives you proper, realistic returns, but ensures you're always on the correct side of the price
        Pretty good, moves quickly away from the current price with higher volitility
    '''
    match side:
        case 'BID':
            # mean = 0, std = volatility, but only take NEGATIVE log-returns
            a, b = -np.inf, 0
            log_return = truncnorm.rvs(a, b, loc=0, scale=volatility)
            return current_price * np.exp(log_return)
        case 'ASK':
            a, b = 0, np.inf
            log_return = truncnorm.rvs(a, b, loc=0, scale=volatility)
            return current_price * np.exp(log_return)


current_price = 1.00

buy_prices = [beta_price(current_price, 'BID') for _ in range(10000)]
sell_prices = [beta_price(current_price, 'ASK') for _ in range(10000)]

plt.hist(buy_prices, bins=1000, alpha=0.5, label='Buy Orders')
plt.hist(sell_prices, bins=1000, alpha=0.5, label='Sell Orders')
plt.axvline(current_price, color='black', linestyle='--', label='Current Price')
plt.legend()
plt.title("Buy vs Sell Order Price Distribution")
plt.xlabel("Price")
plt.ylabel("Frequency")
plt.show()