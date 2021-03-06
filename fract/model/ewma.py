#!/usr/bin/env python

import logging

import numpy as np

from .sieve import LRFeatureSieve


class Ewma(object):
    def __init__(self, config_dict):
        self.__logger = logging.getLogger(__name__)
        self.__alpha = config_dict['model']['ewma']['alpha']
        self.__sigma_band = config_dict['model']['ewma']['sigma_band']
        self.__lrfs = LRFeatureSieve(
            type=config_dict['feature']['type'], drop_zero=False
        )

    def detect_signal(self, history_dict, pos=None, contrary=False):
        best_f = self.__lrfs.extract_best_feature(history_dict=history_dict)
        sig_dict = self._ewm_stats(series=best_f['series'])
        sig_side = (
            'short' if sig_dict['ewma'] * [1, -1][int(contrary)] < 0
            else 'long'
        )
        if sig_dict['ewmbb'][1] < 0 or sig_dict['ewmbb'][0] > 0:
            sig_act = sig_side
        else:
            sig_act = None
        sig_log_str = '{:^40}|'.format(
            '{0:>3}[{1:>3}]:{2:>9}{3:>18}'.format(
                self.__lrfs.code, best_f['granularity_str'],
                '{:.1g}'.format(sig_dict['ewma']),
                np.array2string(
                    sig_dict['ewmbb'],
                    formatter={'float_kind': lambda f: f'{f:.1g}'}
                )
            )
        )
        return {
            'sig_act': sig_act, 'granularity': best_f['granularity'],
            'sig_log_str': sig_log_str, 'sig_ewma': sig_dict['ewma'],
            'sig_ewmbbl': sig_dict['ewmbb'][0],
            'sig_ewmbbu': sig_dict['ewmbb'][1]
        }

    def _ewm_stats(self, series):
        ewm = series.ewm(alpha=self.__alpha)
        ewma = ewm.mean().iloc[-1]
        self.__logger.debug(f'ewma:\t{ewma}')
        ewm_bollinger_band = (
            np.array([-1, 1]) * ewm.std().iloc[-1] * self.__sigma_band
        ) + ewma
        return {'ewma': ewma, 'ewmbb': ewm_bollinger_band}
