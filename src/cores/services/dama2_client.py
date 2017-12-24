# -*- coding: utf-8 -*-
import base64
import json

from src.cores.services import http_client
from src.cores.services.proxy_client import ProxyService
from src.utils import tools


class Dama2Client(object):
    """打码兔API"""

    _HOST = u'http://api.dama2.com:7766/app/'
    _ID = 0
    _KEY = u''
    _USERNAME = u''
    _PASSWORD = u''

    @classmethod
    def __encrypt_password(cls):
        """
        加密用户的密码
        :return: 加密后的密码
        """
        source = cls._KEY + tools.md5(tools.md5(cls._USERNAME) + tools.md5(cls._PASSWORD))
        return tools.md5(source)

    @classmethod
    def __encrypt_sign(cls, param=b''):
        """
        加密签名
        :param param: 加密参数
        :return: 签名
        """
        # source = bytes(cls._KEY, encoding=u'utf8') + bytes(cls._USERNAME, encoding=u'utf8') + param
        source = cls._KEY.encode(encoding=u'utf-8') + cls._USERNAME.encode(encoding=u'utf-8') + param
        return tools.md5(source)[:8]

    @classmethod
    def __post(cls, path, params=None):
        """
        网络POST请求
        :param path: 网站路径
        :param params: 请求参数
        :return: 请求结果
        """
        resp_text = None
        if params is None:
            params = dict()
        url = cls._HOST + path
        if cls._USERNAME == u'test':
            err_count = 0
            while err_count < 10:
                resp_text = (http_client.do_http_post(
                    url=url,
                    data=params,
                    # proxies=ProxyService.get_proxy()
                ))[0]
                if resp_text:
                    break
                err_count += 1
        else:
            resp_text = (http_client.do_http_post(
                url=url,
                data=params
            ))[0]
        return resp_text

    @classmethod
    def get_balance(cls):
        """
        查询余额
        :return: 是正数为余额 如果为负数 则为错误码
        """
        balance = None
        data = {
            u'appID': cls._ID,
            u'user': cls._USERNAME,
            u'pwd': cls.__encrypt_password(),
            u'sign': cls.__encrypt_sign()
        }
        resp_text = cls.__post(u'd2Balance', data)
        if resp_text:
            resp_json = json.loads(resp_text)
            balance = resp_json.get(u'balance') if resp_json.get(u'ret') == 0 else resp_json.get(u'ret')
        return balance

    @classmethod
    def decode_file(cls, file_path, code=200):
        """
        上传验证码文件
        :param file_path: 文件路径
        :param code: 类型码, 查看http://wiki.dama2.com/index.php?n=ApiDoc.Pricedesc
        :return: 是答案为成功 如果为负数 则为错误码
        """
        with open(file_path, 'rb') as f:
            rb_data = f.read()
        return cls.decode_file_buffer(rb_data, code)

    @classmethod
    def decode_file_buffer(cls, rb_data, code=200):
        """
        上传验证码文件流
        :param rb_data: 文件流
        :param code: 类型码, 查看http://wiki.dama2.com/index.php?n=ApiDoc.Pricedesc
        :return: 是答案为成功 如果为负数 则为错误码
        """
        result = {
            u'success': False,
            u'id': None,
            u'value': None
        }
        file_data = base64.b64encode(rb_data)
        data = {
            u'appID': cls._ID,
            u'user': cls._USERNAME,
            u'pwd': cls.__encrypt_password(),
            u'type': code,
            u'fileDataBase64': file_data,
            u'sign': cls.__encrypt_sign(rb_data)
        }
        resp_text = cls.__post(u'd2File', data)
        if resp_text:
            resp_json = json.loads(resp_text)
            if resp_json.get(u'ret') == 0:
                result[u'success'] = True
                result[u'id'] = resp_json[u'id']
                result[u'value'] = resp_json[u'result']
        return result

    @classmethod
    def decode_url(cls, url, code=200):
        """
        根据url地址打码
        :param url: 验证码URL地址
        :param code: 类型码, 查看http://wiki.dama2.com/index.php?n=ApiDoc.Pricedesc
        :return: 是答案为成功 如果为负数 则为错误码
        """
        result = {
            u'success': False,
            u'id': None,
            u'value': None
        }
        data = {
            u'appID': cls._ID,
            u'user': cls._USERNAME,
            u'pwd': cls.__encrypt_password(),
            u'type': code,
            u'url': tools.iquote(url),
            u'sign': cls.__encrypt_sign(url.encode(encoding=u'utf-8'))
        }
        resp_text = cls.__post(u'd2Url', data)
        if resp_text:
            resp_json = json.loads(resp_text)
            if resp_json.get(u'ret') == 0:
                result[u'success'] = True
                result[u'id'] = resp_json[u'id']
                result[u'value'] = resp_json[u'result']
        return result

    @classmethod
    def report_error(cls, result_id):
        """
        报错
        :param result_id: string类型, 由上传打码函数的结果获得
        :return: 0为成功 其他见错误码
        """
        result_id = str(result_id)
        result = None
        data = {
            u'appID': cls._ID,
            u'user': cls._USERNAME,
            u'pwd': cls.__encrypt_password(),
            u'id': result_id,
            u'sign': cls.__encrypt_sign(result_id.encode(encoding=u'utf-8'))
        }
        resp_text = cls.__post(u'd2ReportError', data)
        if resp_text:
            resp_json = json.loads(resp_text)
            result = resp_json.get(u'ret')
        return result
