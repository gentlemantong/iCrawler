# -*- coding: utf-8 -*-


class DamaErrorException(Exception):

    def __init__(self, *args, **kwargs):
        super(DamaErrorException, self).__init__(*args, **kwargs)


class NoDataException(Exception):

    def __init__(self, *args, **kwargs):
        super(NoDataException, self).__init__(*args, **kwargs)


class IPLimitException(Exception):

    def __init__(self, *args, **kwargs):
        super(IPLimitException, self).__init__(*args, **kwargs)


class ConfigurationException(Exception):

    def __init__(self, *args, **kwargs):
        super(ConfigurationException, self).__init__(*args, **kwargs)

