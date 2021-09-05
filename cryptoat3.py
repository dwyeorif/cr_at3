import ccxt
import datetime
import FinanceDataReader as fdr
import pyupbit
import time
import requests

p_exchange = 1160.33  # Exchange rate initial value
binance = ccxt.binance({
'apiKey': '',
'secret': '',
})  # Binance API
upbit = pyupbit.Upbit('', '')  # Upbit API
myToken = ''  # Slack token
ticker = 'EOS'  # Ticker
count = 230  # Order quantity
mount = 1500000  # Order amount
p_standard = 0.02  # Premium standard
p_gap = 0.59  # Premium gap
p_cnt = 299  # Initial count


def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
    headers={"Authorization": "Bearer "+token},
    data={"channel": channel,"text": text}
        )


def get_exchange():
    try:
        today = str(datetime.date.today())
        today = int(today.replace('-', ''))
        today = str(today)
        exchange = fdr.DataReader('USD/KRW', today).iloc[-1, 0]
    except:
        today = 210817
        exchange = fdr.DataReader('USD/KRW', today).iloc[-1, 0]
    post_message(myToken, "#stock", 'Exchange: ' + str(exchange))
    print('환율: ' + str(exchange))
    return exchange


def binance_balance(tk):
    balance = binance.fetch_balance()  # Binance balance
    b_balance = balance[tk]['free']
    return b_balance


def binance_price(tk, p_exchange):
    b_ticker = binance.fetch_ticker(tk+'/USDT')  # Binance current KRW price
    price = b_ticker['close']
    price2 = price * p_exchange
    # print(tk + ' Binance 현재가: ' + str(price2))
    return price2


def binance_usd_price(tk):
    b_ticker = binance.fetch_ticker(tk+'/USDT')  # Binance current USD price
    price = b_ticker['close']
    return price


def binance_buy(tk, cnt):
    order = binance.create_market_buy_order(tk + '/USDT', cnt)  # Binance market buy by count
    print(order)
    # post_message(myToken, "#stock", order)


def binance_sell(tk, cnt):
    order = binance.create_market_sell_order(tk + '/USDT', cnt)  # Binance market sell by count
    print(order)
    # post_message(myToken, "#stock", print(order))


def upbit_price(tk):
    u_price = pyupbit.get_current_price('KRW-' + tk)  # Upbit current KRW price
    return u_price


def upbit_buy(tk, mnt):  # Upbit market buy by amount
    u_ticker = 'KRW-' + tk
    market_price_buy = upbit.buy_market_order(u_ticker, mnt)
    print(market_price_buy)


def upbit_sell(tk, cnt):  # Upbit market sell by count
    u_ticker = 'KRW-' + tk
    market_price_sell = upbit.sell_market_order(u_ticker, cnt)
    print(market_price_sell)


def get_premium(b_price, u_price, tk):  # Current premium
    premium = 100*(u_price-b_price)/u_price
    return premium


while True:
    try:
        if binance_balance('USDT') > (count*binance_usd_price(ticker)+50) and upbit.get_balance('KRW-' + ticker) > count:  # Premium trading
            if get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) > (p_standard+p_gap):  # Above standard
                upbit_sell(ticker, count)
                binance_buy(ticker, count)
                post_message(myToken, "#stock", 'Premium trading: ' + str(round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)) + ' / ' + str(count) + 'ea')
                if binance_balance('USDT') < (count * binance_usd_price(ticker) + 70):  # Reset
                    p_exchange = get_exchange()
                    p_standard = round(get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker), 2)
                    p_standard = (p_standard*0.5) + round(get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker), 2)*0.5
                    post_message(myToken, "#stock", 'Standard: ' + str(p_standard) + ' Reset / Exchange: ' + str(p_exchange))

        if upbit.get_balance('KRW') > mount + 50000 and binance_balance(ticker) > mount/binance_price(ticker, p_exchange):  # Reverse premium trading
            if get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) < (p_standard-p_gap):  # Below standard
                count2 = round(mount / (upbit_price(ticker) + 5), 1)
                upbit_buy(ticker, mount)
                binance_sell(ticker, count2)
                post_message(myToken, "#stock", 'R-premium trading: ' + str(round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)) + ' / ' + str(count2) + 'ea')

        p_cnt = p_cnt + 1

        if p_cnt == 300:
            p_cnt = 0
            p_standard = (p_standard * 0.98) + (get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) * 0.02)
            krw_balance = round(upbit.get_balance('KRW') + binance_balance('USDT')*p_exchange)
            ticker_balance = round(upbit.get_balance('KRW-' + ticker) + binance_balance(ticker))
            now_premium = round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)
            post_message(myToken, "#stock", 'Now: ' + str(now_premium) + ' / Std: ' + str(round(p_standard, 2)) + ' / Exc: ' + str(p_exchange) + '\nCrypto: '+str(ticker_balance) + ' / KRW:  ' + str(krw_balance))
            time.sleep(7)

    except Exception as e:
        post_message(myToken, "#stock", e)
        time.sleep(30)
