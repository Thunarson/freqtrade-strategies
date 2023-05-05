import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from datetime import datetime, timedelta
from typing import Optional

class TheForce_custom(IStrategy):

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: Optional[str], side: str,
                 **kwargs) -> float:
        """
        Customize leverage for each new trade. This method is only called in futures mode.

        :param pair: Pair that's currently analyzed
        :param current_time: datetime object, containing the current datetime
        :param current_rate: Rate, calculated based on pricing settings in exit_pricing.
        :param proposed_leverage: A leverage proposed by the bot.
        :param max_leverage: Max leverage allowed on this pair
        :param entry_tag: Optional entry_tag (buy_tag) if provided with the buy signal.
        :param side: 'long' or 'short' - indicating the direction of the proposed trade
        :return: A leverage amount, which is between 1.0 and max_leverage.
        """
        return 20
    
    can_short=False

    INTERFACE_VERSION = 2

    minimal_roi = {
        "0": 0.2
    }

    stoploss = -0.2

    # Trailing stoploss
    trailing_stop = False
  
    # Optimal timeframe for the strategy.
    timeframe = '15m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 146

    # Optional order type mapping.
    order_types = {
        'exit': 'limit',
        'entry': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': True
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'gtc',
        'exit': 'gtc'
    }
    
    plot_config = {
        # Main plot indicators (Moving averages, ...)
        'main_plot': {
            'tema': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            # Subplots - each dict defines one additional plot
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "RSI": {
                'rsi': {'color': 'red'},
            }
        }
    }
    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """
        
        # Momentum Indicators
        # ------------------------------------

        # Stochastic Fast
        stoch_fast = ta.STOCHF(dataframe,5,3,3)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        dataframe['ema5c'] = ta.EMA(dataframe['close'], timeperiod=5)
   
        # MACD
        macd = ta.MACD(dataframe,12,26,1)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']

        # # EMA - Exponential Moving Average

        dataframe['ema5c'] = ta.EMA(dataframe['close'], timeperiod=5)
        dataframe['ema5o'] = ta.EMA(dataframe['open'], timeperiod=5)

        dataframe['ema10c'] = ta.EMA(dataframe['close'], timeperiod=10)
        dataframe['ema10o'] = ta.EMA(dataframe['open'], timeperiod=10)

        dataframe['sma30c'] = ta.SMA(dataframe['close'], timeperiod=30)
        dataframe['sma30o'] = ta.SMA(dataframe['open'], timeperiod=30)
  
        return dataframe
        

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (
                    (dataframe['fastk'] >= 20) & (dataframe['fastk'] <= 80)
                    &
                    (dataframe['fastd'] >= 20) & (dataframe['fastd'] <= 80)
                )
                &
                (
                    (dataframe['macd'] > dataframe['macd'].shift(1))
                    &
                    (dataframe['macdsignal'] > dataframe['macdsignal'].shift(1))
                )
                &
                (
                    (dataframe['close'] > dataframe['close'].shift(1))
                )
                &
                (
                    (dataframe['ema5c'] >= dataframe['ema5o'])
                #    (dataframe['sma30c'] >= dataframe['sma30o'])
                )
                &
                (
                    (dataframe['sma30c'] >= dataframe['sma30c'].shift(30))
                #    (dataframe['sma30c'] >= dataframe['sma30o'])
                )
                
            ),
            'enter_long'] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (
                    (dataframe['fastk'] <= 80)
                    &
                    (dataframe['fastd'] <= 80)
                )
                &
                (
                    (dataframe['macd'] < dataframe['macd'].shift(1))
                    &
                    (dataframe['macdsignal'] < dataframe['macdsignal'].shift(1))
                )
                &
                (
                    (dataframe['ema5c'] < dataframe['ema5o'])
                )
                
            ),
            'exit_long'] = 1
        
        return dataframe
    
