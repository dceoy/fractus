#!/usr/bin/env python
"""
Stream and trade forex with Oanda API

Usage:
    fract init [--debug] [--config <yaml>]
    fract info <info_type> [--debug] [--config <yaml>]
    fract rate [--debug] [--config <yaml>] [--redis]
    fract event [--debug] [--config <yaml>] [--redis]
    fract trade [--debug] [--config <yaml>]
    fract -h|--help
    fract -v|--version

Options:
    -h, --help      Print help and exit
    -v, --version   Print version and exit
    --debug         Execute a command with debug messages
    --config        Set a path to a YAML for configurations [$FRACTUS_YML]
    --list          List accounts
    --redis         Store streaming data in a Redis server

Commands:
    init            Generate a YAML template for configuration
    info            Print information about <info_type>
                    <info_type>: {
                        instruments, prices, history, account, accounts,
                        orders, trades, positions, position, transaction,
                        transaction_history, eco_calendar,
                        historical_position_ratios, historical_spreads,
                        commitments_of_traders, orderbook, autochartists
                    }
    rate            Stream market prices
    event           Stream authorized account's events
    trade           Trade currencies with a simple algorithm
"""

import logging
from docopt import docopt
from .. import __version__
from .config import set_log_config, set_config_yml, read_yaml, write_config_yml
from ..oanda import info
from ..stream import streamer
from ..model import double


def main():
    args = docopt(__doc__, version='fractus {}'.format(__version__))
    set_log_config(debug=args['--debug'])
    logging.debug('args: \n{}'.format(args))

    if args['--config']:
        config_yml = set_config_yml(path=args['<yaml>'])
    else:
        config_yml = set_config_yml()

    if args['init']:
        logging.debug('Initiation')
        write_config_yml(path=config_yml)
    else:
        logging.debug('config_yml: {}'.format(config_yml))
        config = read_yaml(path=config_yml)
        if args['info']:
            logging.debug('Information')
            info.print_info(config,
                            type=args['<info_type>'])
        elif args['rate']:
            logging.debug('Rates Streaming')
            streamer.invoke(stream_type='rate',
                            config=config,
                            use_redis=args['--redis'])
        elif args['event']:
            logging.debug('Events Streaming')
            streamer.invoke(stream_type='event',
                            config=config,
                            use_redis=args['--redis'])
        elif args['trade']:
            logging.debug('Trading')
            double.play(config=config)