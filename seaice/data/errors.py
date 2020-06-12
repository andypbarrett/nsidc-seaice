class SeaIceDataException(Exception):
    pass


class SeaIceDataNoData(SeaIceDataException):
    pass


class IndexNotFoundError(SeaIceDataException):
    pass


class DateOutOfRangeError(SeaIceDataException):
    pass


class YearMonthOutOfRangeError(SeaIceDataException):
    pass


class IncompleteNRTGridsetError(SeaIceDataException):
    pass


class SeaIceDataValueError(ValueError):
    pass


class SeaIceDataTypeError(TypeError):
    pass


class SeaIceDataInvalidSearchPathsError(SeaIceDataTypeError):
    pass
