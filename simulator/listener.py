import urllib.request, json, time

from logger import logger, configure

class Processor:
    conf = json.load(open('conf.json'))

    # Logger configuration
    configure(conf['log']['level_values'][conf['log']['level']],
            conf['log']['dir'], conf['log']['filename'],
            conf['log']['max_filesize'], conf['log']['max_files'])

    params = {
        'last_trade_price': 0.0,
        'purchase_price': 0.0,
        'new_trade_price': 0.0,
        'new_amount_euros': 0.0,
        'initial_amount_euros': conf['settings']['initial_simulator_amount'],
        'nb_coins_got': 0.0
    }

    def process(params):
        # ACHAT INITAL
        if params['last_trade_price'] == 0:
            params['nb_coins_got'] = params['initial_amount_euros'] / params['new_trade_price']
            params['initial_amount_euros'] = 0

        if params['new_trade_price'] > 0:
            # COMPARATEUR
            if params['new_trade_price'] > params['last_trade_price'] and params['nb_coins_got'] > 0 and params['purchase_price'] < params['last_trade_price']:
                # VENTE
                params['new_amount_euros'] = params['new_trade_price'] * params['nb_coins_got']
                params['nb_coins_got'] = 0
                logger.debug(params)
            elif params['new_trade_price'] < params['last_trade_price'] and params['nb_coins_got'] == 0:
                # ACHAT
                params['nb_coins_got'] = params['new_amount_euros'] / params['new_trade_price']
                params['purchase_price'] = params['new_trade_price']
                params['new_amount_euros'] = 0
                logger.debug(params)
        
        params['last_trade_price'] = params['new_trade_price']

    logger.info("Launching ...")

    while True:
        tickerUrl = conf['settings']['urls']['kraken']['ticker']

        with urllib.request.urlopen(tickerUrl + "?pair=XBTEUR") as url:
            data = json.loads(url.read().decode())
            params['new_trade_price'] = float(data['result']['XXBTZEUR']['c'][0])
            process(params)
            time.sleep(conf['settings']['watcher_interval'])