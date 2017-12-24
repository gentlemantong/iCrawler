# -*- coding: utf-8 -*-
import json
import logging

import execjs

from src.config import FLASK_SERVICE_CONFIG, ENVIRONMENT
from src.cores.services import http_client

# 连接配置
service_url = u'http://{0}:{1}/api/phantomJS/getCookiesFromJS'.format(
    FLASK_SERVICE_CONFIG[ENVIRONMENT][u'host'], FLASK_SERVICE_CONFIG[ENVIRONMENT][u'port'])


def browser_execute(js_str):
    """
    使用浏览器对象执行js，获取cookies和页面数据
    :param js_str: js代码
    :return: 执行结果，包括此时的cookies和数据
    """
    result = dict()
    result[u'success'] = False
    result[u'cookies'] = []
    result[u'html'] = None

    if js_str:
        try:
            resp_text = (http_client.do_http_post(url=service_url, data={u'js': js_str}, timeout=60))[0]
            if resp_text:
                result = json.loads(resp_text)
        except Exception as e:
            logging.exception(e.message)
    return result


def js_execute(js_str):
    """
    执行js语句，返回语句的执行结果
    :param js_str: js代码
    :return: 执行结果
    """
    return execjs.eval(js_str)


def call_js_function(js_str, func_name, params=None):
    """
    调用js中指定的方法
    :param js_str: js代码
    :param func_name: 方法名
    :param params: 方法所需的参数。没有则不传此参数，否则以tuple的形式传进来
    :return: 执行结果
    """
    pattern = execjs.compile(js_str)
    if params is None:
        params = tuple()
    params = (func_name,) + params
    return eval('pattern.call{0}'.format(params))
