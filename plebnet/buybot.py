#!/usr/bin/python2
#coding=utf8

import threading, time
import logging
import os
import json
import requests
__offer_check_time__ = 10

coin = None

def check_asks():
    '''
    Periodically checks for asks in the market, and places a bid against it.
    Currently, accepts all asks regardless of asker.
    '''
    
    logging.info('Coin type is: %s' % coin)

    # create get requests for asks
        # data = {'amount': amount+tx_fee, 'destination': address}
        # r = requests.post('http://localhost:8085/wallets/' + self.coin + '/transfer', data=data)
        # transaction_hash = r.json()['txid']
        # logger.log('Transaction successful. transaction_hash: %s' % transaction_hash, 'wallet_controller.pay')
        
    r = requests.get('http://localhost:8085/market/asks')
    # rb = requests.get('http://localhost:8085/market/bids')

    # evaluate each
    asks = r.json()['asks']

    # we focus only on MB-for-BTC asks
    for ask in asks:
        if ask['price_type'] == coin:
            ticks = ask['ticks']

            for tick in ticks:
                price = tick['price'] # should be BTC
                quantity = tick['quantity'] # should be MB
                quantity_type = tick['quantity_type']
                assert tick['price_type'].upper() == coin

                logging.info('Asks: %s %s %s %s'%(price, coin, quantity, quantity_type))                    

                make_bid(price, coin, quantity, quantity_type)

    # _t_check_offers = threading.Timer(__offer_check_time__, check_asks)
    # _t_check_offers.daemon= True
    # _t_check_offers.start()


def make_bid(price, price_type, quantity, quantity_type):
    logging.info("Making a bid:  %s %s %s %s"%(str(price), price_type, str(quantity), quantity_type))

    # make a bid
    data = {
        'price': price+0.0000001,
        'price_type': price_type,
        'quantity': quantity,
        'quantity_type': quantity_type
    }
    r = requests.put('http://localhost:8085/market/bids', data=data)
    logging.info(r.json())
    # return r.json()

if __name__ == "__main__":
    '''
    Initializes check asks. Is called once.
    '''
    logging.basicConfig(format="%(threadName)s:%(message)s", level='NOTSET')

    tribler_wallet_path = os.path.expanduser('~/.Tribler/wallet')
    if os.path.isfile(os.path.join(tribler_wallet_path, 'tbtc_wallet')):
        coin = 'TBTC'
    elif os.path.isfile(os.path.join(tribler_wallet_path, 'btc_wallet')):
        coin = 'BTC'

    while True:
        check_asks()
        time.sleep(60)
    # global _t_check_offers
    # _t_check_offers = threading.Timer(__offer_check_time__, check_asks)
    # _t_check_offers.daemon = True
    # _t_check_offers.start()