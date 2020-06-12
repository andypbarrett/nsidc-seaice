from datetime import date
from functools import wraps
from unittest.mock import patch


class mock_today(object):
    def __init__(self, year, month, day, module, datetime='dt'):
        """Fix the value of datetime.date.today() to easily test functionality that
        depends on the real-world current day.

        year, month, day: mock datetime.date.today() to equal
                          datetime.date(year, month, day)

        module: patch datetime.date within this module

        datetime: the name datetime is imported as within the given module

        """

        self.date = date(year, month, day)
        self.date_class = '{}.{}.date'.format(module, datetime)

    def __call__(self, func):
        @wraps(func)
        def func_wrapper(*args):
            with patch(self.date_class) as mock_date:
                mock_date.today.return_value = self.date
                mock_date.side_effect = lambda *args_, **kw: date(*args_, **kw)
                return func(*args)
        return func_wrapper
