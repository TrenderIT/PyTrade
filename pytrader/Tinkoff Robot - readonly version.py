import os
import json
from tinkoff.invest import (
    Client, 
    MoneyValue, 
    OrderDirection, 
    OrderType, 
    Quotation
)
from tinkoff.invest.services import Services
import math
import logging
from sys import argv

logging.basicConfig(filename='tinkoff_robot.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)

TOKEN = os.environ["INVEST_TOKEN"]
#TOKEN = 'XXX'
FIGI_TCSG = 'BBG00QPYJ5H0'
FIGI_SBER = 'BBG004730N88'

def cast_money(v):
    """
    https://tinkoff.github.io/investAPI/faq_custom_types/
    :param v:
    :return:
    """
    return v.units + v.nano / 1e9 # nano - 9 нулей

def get_strategy():
    if len(argv) > 1:
        return json.load(argv[1])
    else:
        strategy_json = """
        {
            "account": "12312332345",
            "portfolio": [
                {"figi": "BBG004730JJ5", "ratio": 0.2},
                {"figi": "BBG004730N88", "ratio": 0.4},
                {"figi": "BBG00QPYJ5H0", "ratio": 1.2},
                {"figi": "FG0000000000", "ratio": 0.2}
            ],
            "not_loaded_ratio": 0.5    
        }
        """
        return json.loads(strategy_json)


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def bald(s):
    return color.BOLD + s + color.END

def process_figi(client, figi, figi_data, total_amount):
    print(bald('Processing figi ' + figi))
    print('figi: ', figi, ', ', figi_data)
    current_lots = math.floor(figi_data['quantity'] / figi_data['lot'])
    target_lots = math.floor(total_amount * figi_data['ratio'] / figi_data['price'] / figi_data['lot'])
    logging.info('Process figi '+ figi)
    
    if target_lots == current_lots:
        return
    if target_lots > current_lots:
        direction = OrderDirection.ORDER_DIRECTION_BUY
    if target_lots < current_lots:
        direction = OrderDirection.ORDER_DIRECTION_SELL
        
#!!!!! перепроверить необходимость abs!!!!!!    
#     order = sb.post_sandbox_order(
#         figi = figi, 
#         quantity = abs(target_lots - current_lots),
#         account_id = ACCOUNT,
#         order_id = datetime.now().strftime("%Y-%m-%dT %H:%M:%S"),
#         direction = direction,
#         order_type = OrderType.ORDER_TYPE_MARKET
#     )
        
    print('delta_quantity:', target_lots - current_lots)    
    
with Client(TOKEN) as client:
    strategy = get_strategy()
    try:
        strategy["account"] = os.environ["INVEST_ACCOUNT_ID"]
    except:
        ACCOUNT = strategy["account"]
    
    #ACCOUNT = 'XXX'
    
    #print(bald('accounts'))
    #logging.info(client.users.get_accounts())
    
    #print(bald('info'))
    #print(client.users.get_info())
    
    #tariff = client.users.get_user_tariff()
    #print('tariff', tariff)

    print('')
    
    portfolio = client.operations.get_portfolio(account_id=ACCOUNT)
    print(bald("porfolio= "), portfolio) #Новый счет Робот
    #print(bald("porfolio figies= "), [position.figi for position in portfolio.positions])
    
    positions = client.operations.get_positions(account_id=ACCOUNT)
    if positions.money[0].currency != 'rub':
        assert "Первый счет нерублевый"
    print(bald("positions= "), positions) 
    print(bald('money='), cast_money(positions.money[0]))
    
    total_amount = cast_money(portfolio.total_amount_shares) + cast_money(portfolio.total_amount_bonds) + cast_money(portfolio.total_amount_etf) + cast_money(portfolio.total_amount_currencies) + cast_money(portfolio.total_amount_futures)
    print(bald('total amount='), total_amount)
    
    current_portfolio = portfolio.positions
    
    #Проверка входных данных на консистентность
    #Проверка на неотрицательность
    optimal_portfolio = strategy["portfolio"]
    for position in optimal_portfolio:
        if position["ratio"] < 0:
            logging.error("Ошибка в данных стратегии - доля отрицательная:", position["figi"], position["ratio"])
            assert False

    #Проверка наличия коэффициентов
    ratio_sum = sum([position['ratio'] for position in optimal_portfolio])
    if ratio_sum==0:
        logging.error("Ошибка в данных стратегии - сумма долей нулевая")
        assert False

    #Сбор данных для расчета
    relevant_instruments = {}  
    
    relevant_instruments['USD000UTSTOM'] = {}   #USD 
    
    for position in optimal_portfolio:
        relevant_instruments[position["figi"]] = {}
        
    for position in current_portfolio:    
        relevant_instruments[position.figi] = {}
        
    for instrument in relevant_instruments:
        relevant_instruments[instrument] = {
            "ratio" : 0, 
            "quantity": 0
        }  
        
    for position in current_portfolio:    
        relevant_instruments[position.figi]["quantity"] = cast_money(position.quantity)
    
    for position in positions.securities:
        #relevant_instruments[position.figi]["balance"] = position.balance,
        relevant_instruments[position.figi]["blocked"] = position.blocked
    
    for position in optimal_portfolio:
        relevant_instruments[position["figi"]]["ratio"] += position["ratio"]*(1-strategy["not_loaded_ratio"])/ratio_sum

    #Чтение цен релевантных для алгоритма инструментов
    relevant_figies = [*relevant_instruments.keys()]
    last_prices = client.market_data.get_last_prices(figi=relevant_figies).last_prices

    #USD000UTSTOM_price = client.market_data.get_last_prices(figi=['USD000UTSTOM'])
    #usdrub = cast_money(USD000UTSTOM_price.last_prices[0].price)
    #Экономим вызовы API 
    for figi_price in last_prices:
        if figi_price.figi == 'USD000UTSTOM':
            usdrub = cast_money(figi_price.price)
    print('usdrub=', usdrub)    
    
    for figi_price in last_prices:
        relevant_instruments[figi_price.figi]['price'] = cast_money(figi_price.price)
    
    #Чтение параметров инструментов
    shares = client.instruments.shares()
    bonds = client.instruments.bonds()
    currencies = client.instruments.currencies()  
    all_instruments = shares.instruments + bonds.instruments + currencies.instruments
    
    for instrument in all_instruments:
        if instrument.figi in relevant_instruments.keys():
            relevant_instruments[instrument.figi]['lot'] = instrument.lot
            relevant_instruments[instrument.figi]['name'] = instrument.name  
            relevant_instruments[instrument.figi]['ticker'] = instrument.ticker 
            relevant_instruments[instrument.figi]['currency'] = instrument.currency
            if instrument.currency=='usd':
                relevant_instruments[figi_price.figi]['price_rub'] = relevant_instruments[figi_price.figi]['price'] * usdrub
    
    print(bald('relevant instruments = '))   
    for figi in relevant_instruments:
        #print('figi=', figi, ', ', relevant_instruments[figi])
        if figi!='FG0000000000' and figi!='USD000UTSTOM':
            process_figi(client, figi, relevant_instruments[figi], total_amount)