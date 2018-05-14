# -*- coding: utf-8 -*-
import cloudomate


from appdirs import *

from cloudomate import wallet as wallet_util
from cloudomate.wallet import Wallet
from cloudomate.cmdline import providers as cloudomate_providers
from cloudomate.hoster.vps.clientarea import ClientArea
from cloudomate.util.settings import Settings as AccountSettings

from plebnet.agent.dna import DNA
from plebnet.agent.config import PlebNetConfig
from plebnet.controllers import market_controller
from plebnet.utilities import logger, system_vals, fake_generator


def child_account(index=None):
    if index:
        account = AccountSettings()
        account.read_settings(
            os.path.join(user_config_dir(), 'child_config' + index + '.cfg'))
    else:
        account = AccountSettings()
        account.read_settings(
            os.path.join(user_config_dir(), 'child_config' + PlebNetConfig().get("child_index") + '.cfg'))
    return account


def status(provider):
    account = child_account()
    return provider.get_status(account)


def get_ip(provider):
    logger.log('get ip: %s' % provider)
    client_area = ClientArea(provider._create_browser(), provider.get_clientarea_url(), child_account())
    logger.log('ca: %s' % client_area.get_services())
    return client_area.get_ip()


def setrootpw(provider, password):
    settings = child_account()
    settings.put('server', 'root_password', password)
    # return provider.set_rootpw(settings)


def options(provider):
    return provider.get_options()


def get_network_fee():
    return wallet_util.get_network_fee()


def pick_provider(providers):
    provider = DNA.choose_provider(providers)
    print("pick: %s" % provider)
    gateway = cloudomate_providers['vps'][provider].get_gateway()
    option, price, currency = pick_option(provider)
    btc_price = gateway.estimate_price(
        cloudomate.wallet.get_price(price, currency)) + cloudomate.wallet.get_network_fee()
    return provider, option, btc_price


def pick_option(provider):
    """
    Pick most favorable option at a provider. For now pick cheapest option
    :param provider:
    :return: (option, price, currency)
    """
    vpsoptions = options(cloudomate_providers['vps'][provider])
    if len(vpsoptions) == 0:

        return

    cheapestoption = 0
    for item in range(len(vpsoptions)):
        if vpsoptions[item].price < vpsoptions[cheapestoption].price:
            cheapestoption = item

    logger.log("test_vpsoptions: %s" % str(vpsoptions[cheapestoption]))

    return cheapestoption, vpsoptions[cheapestoption].price, 'USD'


def update_offer(config):
    if not config.get('chosen_provider'):
        return
    (provider, option, _) = config.get('chosen_provider')
    btc_price = calculate_price(provider, option) * 1.15
    place_offer(btc_price, config)


def calculate_price(provider, option):
    logger.log('provider: %s option: %s' % (provider, option))
    vps_option = options(cloudomate_providers['vps'][provider])[option]
    logger.log('chosen_option: %s' % str(vps_option))

    gateway = cloudomate_providers['vps'][provider].get_gateway()
    btc_price = gateway.estimate_price(
        cloudomate.wallet.get_price(vps_option.price, 'USD')) + cloudomate.wallet.get_network_fee()
    return btc_price


def purchase_choice(config):
    """
    Purchase the cheapest provider in chosen_providers. If buying is successful this provider is moved to bought. In any
    case the provider is removed from choices.
    :param config: config
    :return: success
    """

    (provider, option, _) = config.get('chosen_provider')

    provider_instance = cloudomate_providers['vps'][provider](child_account())
    PlebNetConfig().increment_child_index()
    fake_generator.generate_child_account()

    wallet = Wallet()
    c = cloudomate_providers['vps'][provider]

    configurations = c.get_options()
    option = configurations[option]
    print('option: ' + str(option))

    transaction_hash, _ = provider_instance.purchase(wallet, option)
    if transaction_hash:
        config.get('bought').append((provider, transaction_hash, PlebNetConfig().get('child_index')-1))
        config.set('chosen_provider', None)
    else:
        logger.log("Insufficient funds")
        return None, provider
    if provider not in config.get('excluded_providers'):
        config.get('excluded_providers').append(provider)
    return transaction_hash, provider


def place_offer(chosen_est_price, config):
    """
    Sell all available MC for the chosen estimated price on the Tribler market.
    :param config: config
    :param chosen_est_price: Target amount of BTC to receive
    :return: success of offer placement
    """
    available_mc = market_controller.get_mc_balance()
    if available_mc == 0:
        logger.log("No MC available")
        return False
    config.bump_offer_date()
    config.set('last_offer', {'BTC': chosen_est_price, 'MC': available_mc})
    price_per_unit = chosen_est_price / float(available_mc)
    return market_controller.put_ask(price=price_per_unit,
                                     price_type='BTC',
                                     quantity=available_mc,
                                     quantity_type='MC',
                                     timeout=system_vals.TIME_IN_HOUR)
