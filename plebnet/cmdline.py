import sys
import time
from argparse import ArgumentParser

from plebnet.agent.config import PlebNetConfig
from plebnet.agent.dna import DNA
from plebnet.controllers import electrum_controller
from plebnet.utilities import logger, fake_generator
from plebnet.communication.irc import irc_handler
from plebnet.settings import plebnet_settings as setup
from plebnet.agent import core as agent


def execute(cmd=sys.argv[1:2]):
    parser = ArgumentParser(description="Plebnet")

    subparsers = parser.add_subparsers(dest="command")

    # create the setup subcommand
    parser_list = subparsers.add_parser("setup", help="Run the setup of PlebNet")
    parser_list.set_defaults(func=execute_setup)

    # create the check subcommand
    parser_list = subparsers.add_parser("check", help="Checks if the plebbot is able to clone")
    parser_list.set_defaults(func=execute_check)

    # create the irc subcommand
    parser_list = subparsers.add_parser("irc", help="Provides access to the IRC client")
    parser_list.set_defaults(func=execute_irc)

    args = parser.parse_args(cmd)
    args.func()


def execute_setup(cmd=sys.argv[2:]):
    logger.log("Setting up PlebNet")

    # Prepare Cloudomate
    fake_generator.generate_child_account()

    # TODO: change --> Prepare plebnet
    config = PlebNetConfig()
    config.set('expiration_date', time.time() + 30 * setup.TIME_IN_DAY)
    config.save()

    # handle the DNA
    dna = DNA()
    dna.read_dictionary()
    dna.write_dictionary()

    # Prepare Electrum
    electrum_controller.create_wallet()

    # Prepare the IRC Client
    irc_handler.init_irc_client()
    irc_handler.start_irc_client()

    logger.success("PlebNet is ready to roll!")


def execute_check(cmd=sys.argv[2:]):
    agent.check()


def execute_irc(cmd=sys.argv[2:]):
    parser = ArgumentParser(description="irc thingies")

    subparsers = parser.add_subparsers(dest="command")
    parser_list = subparsers.add_parser("status", help="Provides information regarding the status of the IRC Client")
    parser_list.set_defaults(func=irc_handler.status_irc_client)

    parser_list = subparsers.add_parser("start", help="Starts the IRC Client ")
    parser_list.set_defaults(func=irc_handler.start_irc_client)

    parser_list = subparsers.add_parser("stop", help="Stops the IRC Client")
    parser_list.set_defaults(func=irc_handler.stop_irc_client)

    parser_list = subparsers.add_parser("restart", help="Restarts the IRC Client ")
    parser_list.set_defaults(func=irc_handler.restart_irc_client)

    args = parser.parse_args(cmd)
    args.func(args)


if __name__ == '__main__':
    execute()
