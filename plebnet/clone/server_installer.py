"""
This file contains all code used to setup a new PlebNet agent on a remote server.

It used the available servers listed in the configuration and tries to install
the latest version of PlebNet on these servers.
"""

import os
import subprocess

from plebnet.controllers import cloudomate_controller
from plebnet.settings import plebnet_settings as setup
from plebnet.utilities import logger


def install_available_servers(config, dna):
    """
    This function checks if any of the bought servers are ready to be installed and installs
    PlebNet on them.
    :param config: The configuration of this Plebbot
    :type config: dict
    :param dna: The DNA of this Plebbot
    :type dna: DNA
    :return: None
    :rtype: None
    """
    bought = config.get('bought')
    logger.log("install: %s" % bought, "install_available_servers")
    for provider, transaction_hash, child_index in list(bought):
        try:
            provider_class = cloudomate_controller.get_vps_providers()[provider]
            ip = cloudomate_controller.get_ip(provider_class, cloudomate_controller.child_account(child_index))
        except BaseException as e:
            logger.log(str(e) + "%s not ready yet" % str(provider), "install_available_servers")
            return

        logger.log("Installing child on %s with ip %s" % (provider, str(ip)))
        if is_valid_ip(ip):
            account_settings = cloudomate_controller.child_account(child_index)
            parentname = '{0}-{1}'.format(account_settings.get('user', 'firstname'),
                                          account_settings.get('user', 'lastname'))
            dna.create_child_dna(provider, parentname, transaction_hash)

            # Save config before entering possibly long lasting process
            config.save()
            rootpw = account_settings.get('server', 'root_password')
            success = _install_server(ip, rootpw)

            # Reload config in case install takes a long time
            config.load()
            config.get('installed').append({provider: success})
            if [provider, transaction_hash, child_index] in config.get('bought'):
                config.get('bought').remove([provider, transaction_hash, child_index])
            config.save()


def is_valid_ip(ip):
    """
    This methods checks if the provided ip-address is valid.
    :param ip: The ipadress to check
    :type ip: String
    :return: True/False
    :rtype: Boolean
    """
    if ip:
        pieces = ip.strip().split('.')
        if len(pieces) != 4:
            return False
        try:
            if 0 <= int(pieces[1]) < 256:
                return all(0 <= int(p) < 256 for p in pieces)
        except ValueError:
            return False
    return False


def _install_server(ip, rootpw):
    """
    This function starts the actual installation routine.
    :param ip: The ip-address of the remote server
    :type ip: String
    :param rootpw: The root password of the remote server
    :type rootpw: String
    :return: The exit status of the installation
    :rtype: Integer
    """
    settings = setup.get_instance()
    home = settings.plebnet_home()
    if settings.wallets_testnet():
        script_path = os.path.join(home, "plebnet/clone/create-child-testnet.sh")
    else:
        script_path = os.path.join(home, "plebnet/clone/create-child.sh")
    logger.log('tot_path: %s' % script_path)
    command = 'bash %s %s %s' % (script_path, ip.strip(), rootpw.strip())
    logger.log("Running %s" % command, '_install_server')
    success = subprocess.call(command, shell=True, cwd=home)
    if success:
        logger.log("Installation successful")
    else:
        logger.log("Installation unsuccessful")
    return success
