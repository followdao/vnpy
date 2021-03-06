"""
Author: Zehua Wei (nanoric)

Load data from a csv file.

Differences to 1.9.2:
    * combine Date column and Time column into one Datetime column

Sample csv file:

```csv
"Datetime","Open","High","Low","Close","Volume"
2010-04-16 09:16:00,3450.0,3488.0,3450.0,3468.0,489
2010-04-16 09:17:00,3468.0,3473.8,3467.0,3467.0,302
2010-04-16 09:18:00,3467.0,3471.0,3466.0,3467.0,203
2010-04-16 09:19:00,3467.0,3468.2,3448.0,3448.0,280
2010-04-16 09:20:00,3448.0,3459.0,3448.0,3454.0,250
2010-04-16 09:21:00,3454.0,3456.8,3454.0,3456.8,109
```

"""

import csv
from datetime import datetime

from peewee import chunked

from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import DbBarData, DB
from vnpy.trader.engine import BaseEngine, MainEngine


APP_NAME = "CsvLoader"


class CsvLoaderEngine(BaseEngine):
    """"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.file_path: str = ""

        self.symbol: str = ""
        self.exchange: Exchange = Exchange.SSE
        self.interval: Interval = Interval.MINUTE
        self.datetime_head: str = ""
        self.open_head: str = ""
        self.close_head: str = ""
        self.low_head: str = ""
        self.high_head: str = ""
        self.volume_head: str = ""

    def load(
        self,
        file_path: str,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        datetime_head: str,
        open_head: str,
        close_head: str,
        low_head: str,
        high_head: str,
        volume_head: str,
        datetime_format: str
    ):
        """"""
        vt_symbol = f"{symbol}.{exchange.value}"

        start = None
        end = None
        count = 0

        with open(file_path, "rt") as f:
            reader = csv.DictReader(f)

            db_bars = []

            for item in reader:
                dt = datetime.strptime(item[datetime_head], datetime_format)

                db_bar = {
                    "symbol": symbol,
                    "exchange": exchange.value,
                    "datetime": dt,
                    "interval": interval.value,
                    "volume": item[volume_head],
                    "open_price": item[open_head],
                    "high_price": item[high_head],
                    "low_price": item[low_head],
                    "close_price": item[close_head],
                    "vt_symbol": vt_symbol,
                    "gateway_name": "DB"
                }

                db_bars.append(db_bar)

                # do some statistics
                count += 1
                if not start:
                    start = db_bar["datetime"]

        end = db_bar["datetime"]

        # Insert into DB
        with DB.atomic():
            for batch in chunked(db_bars, 50):
                DbBarData.insert_many(batch).on_conflict_replace().execute()

        return start, end, count
