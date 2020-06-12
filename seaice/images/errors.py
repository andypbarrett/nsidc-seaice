class SeaIceImagesError(Exception):
    pass


class SeaIceImagesBadConfiguration(SeaIceImagesError):
    pass


class SeaIceImagesBadCommandLineArguments(SeaIceImagesError):
    pass


class SeaIceImagesNoData(SeaIceImagesError):
    pass


class SeaIceImagesNotImplementedError(SeaIceImagesError):
    pass
