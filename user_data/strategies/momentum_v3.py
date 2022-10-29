from pandas import DataFrame
from functools import reduce
from freqtrade.strategy import IStrategy
from freqtrade.strategy import IntParameter
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class Momentum(IStrategy):

    minimal_roi = {
      "0": 0.464,
      "474": 0.127,
      "1153": 0.036,
      "1977": 0
    }

    stoploss = -0.25
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.055
    trailing_only_offset_is_reached = True

    timeframe = "1h"
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False
    process_only_new_candles = True
    startup_candle_count = 100

    buy_params = {
        "stoch_lower_bound": 15
    }

    sell_params = {
        "sell_rsi": 80,
        "stoch_upper_bound": 85
    }

    stoch_lower_bound = IntParameter(0, 40, default=15, space='buy', optimize=True, load=True)

    sell_rsi = IntParameter(60, 100, default=80, space='sell', optimize=True, load=True)
    stoch_upper_bound = IntParameter(
        60, 100, default=70, space='sell', optimize=True, load=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ADX
        # dataframe['ADX'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=14)

        # Stochastic RSI
        stoch = ta.STOCHRSI(dataframe, timeperiod=14)
        dataframe['stoch_fastk'] = stoch['fastk']
        dataframe['stoch_fastd'] = stoch['fastd']

        # # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(qtpylib.crossed_above(dataframe['stoch_fastk'], dataframe['stoch_fastd']))
        conditions.append(dataframe['plus_di'] > dataframe['minus_di'])
        conditions.append(dataframe['stoch_fastk'] < self.stoch_lower_bound.value)

        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(qtpylib.crossed_below(dataframe['rsi'], self.sell_rsi.value) | (qtpylib.crossed_below(
            dataframe['stoch_fastk'], dataframe['stoch_fastd']) & (dataframe['stoch_fastk'] > self.stoch_upper_bound.value)))
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'sell']=1

        return dataframe
