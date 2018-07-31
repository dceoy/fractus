#!/usr/bin/env python

import json
import os
import logging
import sqlite3
import oandapy
import pandas as pd
import pandas.io.sql as pdsql
import yaml
from ..cli.util import FractError, read_config_yml
from .streamer import StorageStreamer


def invoke_stream(config_yml, target, instruments, sqlite_path=None,
                  use_redis=False, redis_host=None, redis_port=6379,
                  redis_db=0, redis_maxl=1000):
    logger = logging.getLogger(__name__)
    logger.info('Streaming')
    cf = read_config_yml(path=config_yml)
    insts = (instruments if instruments else cf['instruments'])
    streamer = StorageStreamer(
        target=target, sqlite_path=sqlite_path, use_redis=use_redis,
        redis_host=redis_host, redis_port=redis_port, redis_db=redis_db,
        redis_maxl=redis_maxl, environment=cf['oanda']['environment'],
        access_token=cf['oanda']['access_token'],
    )
    streamer.invoke(
        account_id=cf['oanda']['account_id'], instruments=','.join(insts),
        ignore_heartbeat=True
    )


def track_rate(config_yml, instruments, granularity, count, sqlite_path=None):
    logger = logging.getLogger(__name__)
    logger.info('Rate tracking')
    cf = read_config_yml(path=config_yml)
    oanda = oandapy.API(
        environment=cf['oanda']['environment'],
        access_token=cf['oanda']['access_token']
    )
    candles = {
        inst: [
            d for d
            in oanda.get_history(
                account_id=cf['oanda']['account_id'], instrument=inst,
                candleFormat='bidask', granularity=granularity, count=count
            )['candles'] if d['complete']
        ] for inst in (instruments or cf['instruments'])
    }
    if sqlite_path:
        df = pd.concat([
            pd.DataFrame.from_dict(
                d
            ).drop(
                ['complete'], axis=1
            ).assign(
                instrument=i
            )
            for i, d in candles.items()
        ]).reset_index(
            drop=True
        )
        logger.debug('df.shape: {}'.format(df.shape))
        if os.path.isfile(sqlite_path):
            with sqlite3.connect(sqlite_path) as con:
                df_diff = df.merge(
                    pdsql.read_sql(
                        'SELECT instrument, time FROM candle;', con
                    ).assign(
                        in_db=True
                    ),
                    on=['instrument', 'time'], how='left'
                ).pipe(
                    lambda d: d[d['in_db'].isnull()].drop(['in_db'], axis=1)
                ).reset_index(
                    drop=True
                )
                logger.debug('df_diff:{0}{1}'.format(os.linesep, df_diff))
                pdsql.to_sql(
                    df_diff, 'candle', con, index=False, if_exists='append'
                )
        else:
            with open(os.path.join(os.path.dirname(__file__),
                                   '../static/create_tables.sql'),
                      'r') as f:
                sql = f.read()
            with sqlite3.connect(sqlite_path) as con:
                con.executescript(sql)
                logger.debug('df:{0}{1}'.format(os.linesep, df))
                pdsql.to_sql(
                    df, 'candle', con, index=False, if_exists='append'
                )
    else:
        print(json.dumps(candles))


def print_info(config_yml, instruments, type='accounts'):
    logger = logging.getLogger(__name__)
    logger.info('Information')
    cf = read_config_yml(path=config_yml)
    oanda = oandapy.API(
        environment=cf['oanda']['environment'],
        access_token=cf['oanda']['access_token']
    )
    account_id = cf['oanda']['account_id']
    cs_instruments = ','.join(instruments)
    if type == 'instruments':
        info = oanda.get_instruments(account_id=account_id)
    elif type == 'prices':
        info = oanda.get_prices(account_id=account_id,
                                instruments=cs_instruments)
    elif type == 'account':
        info = oanda.get_account(account_id=account_id)
    elif type == 'accounts':
        info = oanda.get_accounts()
    elif type == 'orders':
        info = oanda.get_orders(account_id=account_id)
    elif type == 'trades':
        info = oanda.get_trades(account_id=account_id)
    elif type == 'positions':
        info = oanda.get_positions(account_id=account_id)
    elif type == 'position':
        info = oanda.get_position(account_id=account_id,
                                  instruments=cs_instruments)
    elif type == 'transaction':
        info = oanda.get_transaction(account_id=account_id)
    elif type == 'transaction_history':
        info = oanda.get_transaction_history(account_id=account_id)
    elif type == 'eco_calendar':
        info = oanda.get_eco_calendar()
    elif type == 'historical_position_ratios':
        info = oanda.get_historical_position_ratios()
    elif type == 'historical_spreads':
        info = oanda.get_historical_spreads()
    elif type == 'commitments_of_traders':
        info = oanda.get_commitments_of_traders()
    elif type == 'orderbook':
        info = oanda.get_orderbook()
    elif type == 'autochartist':
        info = oanda.get_autochartist()
    else:
        raise FractError('invalid info type: {}'.format(type))
    logger.debug('Print information: {}'.format(type))
    print(yaml.dump(info, default_flow_style=False))
