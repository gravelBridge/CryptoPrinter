import robin_stocks.robinhood as rh
import pyotp
import openai
import os
from datetime import datetime, timedelta
import time
import requests
import re

openai.api_key = os.getenv("OPENAI_API_KEY")
totp  = pyotp.TOTP(os.getenv("TOTP")).now()
login = rh.login(os.getenv("ROBINHOOD_EMAIL"), os.getenv("ROBINHOOD_PASSWORD"), mfa_code=totp)
symbols = ["BTC", "ETH", "BNB", "XRP", "ADA"]

PROMPT_FOR_AI = f"""
You are in control of my crypto trading profile. You should take into consideration the factors you have to determine the best trade. Here is the info:

You can execute these commands:

1. buy_crypto_price(symbol, amount) This will buy the specified dollars of the specified cryptocurrency.
2. buy_crypto_limit(symbol, amount, limit) This will set a limit order to buy the specified dollars of the specified cryptocurrency if it reaches the specified limit.
3. sell_crypto_price(symbol, amount) This will sell the specified dollars of the specified cryptocurrency.
4. sell_crypto_limit(symbol, amount, limit) This will set a limit order to sell the specified dollars of the specified cryptocurrency if it reaches the specified limit.
5. cancel_order(orderId) This will cancel the specified order.
6. do_nothing() Use this when you don't see any necessary changes.

You also have access to these data:

1. Crypto Info (symbol, ask_price, bid_price, high_price, low_price, volume)
2. Balance
3. Open Orders (id, type, side, quantity, price)
4. Positions (symbol, quantity, average_buy_price, cost_basis, direct_portfolio_percentage)
5. Historical Data (begins_at, open_price, close_price, high_price, low_price, volume)
6. News Headlines

The current date and time is {datetime.now().isoformat()}

You are called once every 30 minutes, keep this in mind.

The only cryptos you can trade are BTC, ETH, BNB, XRP and ADA.
"""

past_trades = []

def record_trade(action, symbol, amount, limit=None):
    trade_info = {
        "action": action,
        "symbol": symbol,
        "amount": amount,
        "time": datetime.now().isoformat(),
    }
    if limit is not None:
        trade_info["limit"] = limit
    past_trades.append(trade_info)
    if len(past_trades) > 10:  # keep only the last 10 trades
        past_trades.pop(0)

def get_crypto_infos():
    infos = {}
    for symbol in symbols:
        quote = rh.get_crypto_quote(symbol)
        useful_info = {
            'symbol': quote['symbol'],
            'ask_price': quote['ask_price'],
            'bid_price': quote['bid_price'],
            'high_price': quote['high_price'],
            'low_price': quote['low_price'],
            'volume': quote['volume']
        }
        infos[symbol] = useful_info
    return infos

def get_balance():
    profile = rh.profiles.load_account_profile()
    return float(profile["buying_power"])-1  # returns total account equity minus one for fees

def buy_crypto_price(symbol, amount):
    amount = float(amount)
    res = rh.order_buy_crypto_by_price(symbol, amount)
    record_trade("buy_crypto_price", symbol, amount)
    print(res)

def buy_crypto_limit(symbol, amount, limit):
    amount = float(amount)
    limit = float(limit)
    res = rh.order_buy_crypto_limit_by_price(symbol, amount, limit)
    record_trade("buy_crypto_limit", symbol, amount, limit)
    print(res)

def sell_crypto_price(symbol, amount):
    amount = float(amount)
    res = rh.order_sell_crypto_by_price(symbol, amount)
    record_trade("sell_crypto_price", symbol, amount)
    print(res)

def sell_crypto_limit(symbol, amount, limit):
    amount = float(amount)
    limit = float(limit)
    res = rh.order_sell_crypto_limit_by_price(symbol, amount, limit)
    record_trade("sell_crypto_limit", symbol, amount, limit)
    print(res)

def get_open_orders():
    positions_data = rh.get_all_open_crypto_orders()
    
    useful_infos = []
    for position in positions_data:
        useful_info = {
            'id': position['id'],
            'type': position['type'],
            'side': position['side'],
            'quantity': position['quantity'],
            'price': position['price']
        }
        useful_infos.append(useful_info)
    return useful_infos

def get_positions():
    positions_data = rh.crypto.get_crypto_positions()

    useful_infos = []
    for position in positions_data:
        if float(position['quantity']) > 0:  # we only want open positions with a quantity greater than 0
            currency_code = position['currency']['code']
            # Fetch current price for this cryptocurrency
            current_price_data = rh.crypto.get_crypto_quote(currency_code)
            current_price = float(current_price_data['mark_price'])
            # Convert quantity to dollar amount
            quantity = float(position['quantity'])
            dollar_amount = quantity * current_price

            useful_info = {
                'symbol': currency_code,
                'quantity': quantity,
                'dollar_amount': dollar_amount,
            }
            useful_infos.append(useful_info)
    print(useful_infos)
    return useful_infos

def cancel_order(orderId):
    rh.cancel_crypto_order(orderId)

def get_historical_data():
    # Define the start and end times
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    historicals = {}

    for symbol in symbols:
        # Fetch the historical data
        data = rh.crypto.get_crypto_historicals(symbol,
                                                interval='10minute',
                                                bounds='24_7',
                                                span="hour")

        # Filter out unnecessary information
        useful_data = []
        for entry in data:
            useful_entry = {
                'begins_at': entry['begins_at'],
                'open_price': entry['open_price'],
                'close_price': entry['close_price'],
                'high_price': entry['high_price'],
                'low_price': entry['low_price'],
                'volume': entry['volume'],
            }
            useful_data.append(useful_entry)
        
        historicals[symbol] = useful_data

    return historicals

def get_all_crypto_news():
    API_KEY = os.getenv("NEWSAPI_KEY")
    all_news = {}

    for symbol in symbols:
        url = f'https://newsapi.org/v2/everything?q={symbol}&apiKey={API_KEY}'
        response = requests.get(url)
        data = response.json()
        
        news_data = []
        try:
            for article in data['articles'][:3]:  # Limit to top 3 articles
                news_data.append({
                    'title': article['title'],
                    'source': article['source']['name'],
                })
            all_news[symbol] = news_data
        except:
            return all_news

    return all_news

def get_trade_advice():
    # Get all the necessary information
    crypto_info = get_crypto_infos()
    balance = get_balance()
    positions = get_positions()
    news = get_all_crypto_news()
    open_orders = get_open_orders()
    past_trade_info = '\n'.join([str(trade) for trade in past_trades])

    # Convert the info into a format suitable for the AI prompt
    info_str = f"Crypto Info: {crypto_info}\nBalance: {balance}\nPositions: {positions}\nNews: {news}\nOpen Orders: {open_orders}\nPast Trades: {past_trade_info}"
    prompt = PROMPT_FOR_AI + "\n\n" + info_str
    user_prompt = """
What should we do to make the most amount of profit based on the info?

buy_crypto_price(symbol, amount) This will buy the specified dollars of the specified cryptocurrency.
buy_crypto_limit(symbol, amount, limit) This will set a limit order to buy the specified dollars of the specified cryptocurrency if it reaches the specified limit.
sell_crypto_price(symbol, amount) This will sell the specified dollars of the specified cryptocurrency.
sell_crypto_limit(symbol, amount, limit) This will set a limit order to sell the specified dollars of the specified cryptocurrency if it reaches the specified limit.
cancel_order(orderId) This will cancel the specified order.
do_nothing() Use this when you don't see any necessary changes.

CRITICAL: RESPOND IN ONLY THE ABOVE FORMAT. EXAMPLE: buy_crypto_price("BTC", 30). ONLY RESPOND WITH ONE COMMAND.
    """

    # Feed the prompt to the AI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature = 0.2,
    )
    res = response.choices[0].message["content"]
    res = res.replace("\\", "")
    return res

def execute_response(response):
    match = re.match(r'(\w+)\((.*?)\)', response)
    if match:
        command = match.group(1)
        args = [arg.strip().strip('\"') for arg in match.group(2).split(',')]  # remove surrounding quotation marks
        if len(args) == 1:
            print("Doing nothing...")
            return
        command_map = {
            "buy_crypto_price": buy_crypto_price,
            "buy_crypto_limit": buy_crypto_limit,
            "sell_crypto_price": sell_crypto_price,
            "sell_crypto_limit": sell_crypto_limit,
            "cancel_order": cancel_order,
            "do_nothing": lambda: None  # no action needed
        }
        function_to_execute = command_map.get(command)  # retrieves the function from command_map dictionary
        if function_to_execute:
            print(f"Executing command {function_to_execute} with args {args} in 5 seconds.")
            time.sleep(5)
            function_to_execute(*args)  # executes the function with its arguments
        else:
            print("Invalid command:", command)
    else:
        print("Invalid response, retrying:", response)
        time.sleep(10)
        execute_response(get_trade_advice())

while True:
    execute_response(get_trade_advice())
    time.sleep(1800)
