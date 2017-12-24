# -*- coding: utf-8 -*-
from src.config import PROXY_CONFIG, ENVIRONMENT
from src.cores.services import http_client


class ProxyService(object):

    _PROXY_POOL = []
    _COUNT = 5

    @classmethod
    def get_proxy(cls, proxy_type=u'abuyun', data_type=u'qy_data1'):
        """
        通过代理服务接口获取代理
        :param proxy_type: 代理类型
        :param data_type: 使用代理的数据类型
        :return: 代理
        """
        if cls._PROXY_POOL:
            return cls._PROXY_POOL.pop(0)
        else:
            url = u'http://{0}:{1}/proxy/get_proxy'.format(
                PROXY_CONFIG[ENVIRONMENT][u'host'], PROXY_CONFIG[ENVIRONMENT][u'port'])
            params = {
                u'proxy_type': proxy_type,
                u'data_type': data_type,
                u'count': cls._COUNT
            }
            resp_text = (http_client.do_http_get(url, params=params))[0]
            if resp_text:
                proxy_list = resp_text.split(u'\n')
                for proxy in proxy_list:
                    if proxy.strip():
                        item = dict()
                        item[u'https'] = item[u'http'] = u'http://{0}'.format(proxy)
                        cls._PROXY_POOL.append(item)
            return cls.get_proxy(proxy_type=proxy_type, data_type=data_type)

    @classmethod
    def get_dynamic_proxy(cls):
        """
        获取动态代理
        :return: 代理
        """
        return dict.fromkeys([u'http', u'https'], u'http://H8XE867MS30JN71D:9A54D0F23D646DDC@http-dyn.abuyun.com:9020')
