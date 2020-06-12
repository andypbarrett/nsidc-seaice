from datetime import date
from functools import wraps
from unittest.mock import patch


class mock_today(object):
    def __init__(self, year, month, day):
        self.date = date(year, month, day)

    def __call__(self, func):
        @wraps(func)
        def func_wrapper(*args):
            with patch('seaice.nasateam.trends.dt.date') as mock_date:
                mock_date.today.return_value = self.date
                mock_date.side_effect = lambda *args_, **kw: date(*args_, **kw)
                return func(*args)
        return func_wrapper
