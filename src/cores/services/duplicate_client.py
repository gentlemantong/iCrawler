# -*- coding: utf-8 -*-
from src.config import FLASK_SERVICE_CONFIG, ENVIRONMENT

from src.cores.services import http_client


def check_exist(type_name, key):
    """
    检查数据是否重复
    :param type_name: 数据类型
    :param key: 关键字
    :return: 检查结果
    """
    url = u'http://{0}:{1}/api/SpiderDuplicate/check'.format(
        FLASK_SERVICE_CONFIG[ENVIRONMENT][u'host'], FLASK_SERVICE_CONFIG[ENVIRONMENT][u'port'])
    params = {
        u'type': type_name,
        u'key': key
    }
    resp = (http_client.do_http_get(url, params=params))[0]
    return True if u'true' in resp else False


def put(type_name, key):
    """
    将数据加入查重池
    :param type_name: 数据类型
    :param key: 关键字
    :return: 添加结果
    """
    url = u'http://{0}:{1}/api/SpiderDuplicate/put'.format(
        FLASK_SERVICE_CONFIG[ENVIRONMENT][u'host'], FLASK_SERVICE_CONFIG[ENVIRONMENT][u'port'])
    data = {
        u'type': type_name,
        u'key': key
    }
    return (http_client.do_http_post(url, data=data))[0]
