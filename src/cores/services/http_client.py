# -*- coding: utf-8 -*-
import base64
import logging
import random

import cchardet
import copy
import gevent
import requests
from requests.exceptions import *

from src.utils import tools

_BROWSER_HEADERS = [
    u'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    (u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 '
     u'Safari/537.36 OPR/47.0.2631.71'),
    u'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)',
    u'Opera/9.27 (Windows NT 5.2; U; zh-cn)',
    u'Mozilla/5.0 (Windows; U; Windows NT 5.2) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13',
    u'Mozilla/5.0 (Windows; U; Windows NT 5.2) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13',
    u'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.12) Gecko/20080219 Firefox/2.0.0.12 Navigator/9.0.0.6',
    u'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; 360SE)',
    (u'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; '
     u'Windows NT 5.1; SV1) ;  QIHU 360EE)'),
    (u'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; '
     u'Windows NT 5.1; SV1) ; Maxthon/3.0)'),
    (u'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; TencentTraveler 4.0; '
     u'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1))'),
    (u'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.55.3 (KHTML, like Gecko) '
     u'Version/5.1.5 Safari/534.55.3')
]


def do_http_get(url, params=None, headers=None, timeout=20, cookies=None, proxies=False, encoding=None,
                allow_status=None, err_retry=3, allow_redirects=False):
    """
    GET方法
    :param url: 链接
    :param params: 参数
    :param headers: 请求头
    :param timeout: timeout时间
    :param cookies: cookies
    :param proxies: 代理
    :param encoding: 编码
    :param allow_status: 允许通过的状态码
    :param err_retry: 失败重试的次数
    :param allow_redirects: 重定向参数
    :return: 响应正文 | 响应头 | 响应的cookie
    """
    resp_text = resp_headers = resp_cookies = None

    # 准备请求参数
    if not headers:
        headers = {u'User-Agent': random.choice(_BROWSER_HEADERS)}
    if not headers.get(u'User-Agent'):
        headers[u'User-Agent'] = random.choice(_BROWSER_HEADERS)
    headers = copy.deepcopy(headers)
    headers[u'User-Agent'] += u' {0}'.format(tools.random_char_num(int(tools.random_num(1))))
    if not allow_status:
        allow_status = [200]

    err_count = 0
    resp = None
    while err_count < err_retry:
        try:
            resp = requests.get(
                url=url,
                params=params,
                headers=headers,
                timeout=timeout,
                cookies=cookies,
                proxies=proxies,
                allow_redirects=allow_redirects,
                verify=False
            )
            if resp.status_code in allow_status:
                if not encoding:
                    resp.encoding = cchardet.detect(resp.content)[u'encoding']
                else:
                    resp.encoding = encoding
                resp_text = resp.text
                resp_headers = resp.headers
                resp_cookies = resp.cookies.get_dict()
                if cookies is not None:
                    cookies.update(resp_cookies)
                err_count = err_retry
            else:
                raise HTTPError(u'Invalid status code --> {0}\r\n{1}'.format(resp.status_code, resp.text))
        except Exception as e:
            logging.exception(u'Do http get({0}) error! - {1}'.format(url, e.message))
            if u'429' in repr(e):
                logging.debug(u'Too many requests in current proxy tunnel, sleep for a while...')
                err_count -= 1
            gevent.sleep(3)
        finally:
            if resp:
                try:
                    resp.close()
                except Exception as e:
                    logging.exception(u'failed to close get response! - {0}'.format(e.message))
        err_count += 1
    return resp_text, resp_headers, resp_cookies


def do_http_post(url, data=None, be_json=False, headers=None, timeout=20, cookies=None, proxies=False, encoding=None,
                 allow_status=None, err_retry=3, allow_redirects=False):
    """
    POST方法
    :param url: 链接
    :param data: 请求数据主题
    :param be_json: 是否是json
    :param headers: 请求头
    :param timeout: timeout时间
    :param cookies: cookies
    :param proxies: 代理
    :param encoding: 编码
    :param allow_status: 允许通过的状态码
    :param err_retry: 失败重试的次数
    :param allow_redirects: 重定向参数
    :return: 响应正文 | 响应头 | 响应的cookie
    """
    resp_text = resp_headers = resp_cookies = None

    # 准备请求参数
    if not headers:
        headers = {u'User-Agent': random.choice(_BROWSER_HEADERS)}
    if not headers.get(u'User-Agent'):
        headers[u'User-Agent'] = random.choice(_BROWSER_HEADERS)
    headers = copy.deepcopy(headers)
    headers[u'User-Agent'] += u' {0}'.format(tools.random_char_num(int(tools.random_num(1))))
    if not allow_status:
        allow_status = [200]

    err_count = 0
    resp = None
    while err_count < err_retry:
        try:
            if be_json:
                resp = requests.post(
                    url=url,
                    json=data,
                    headers=headers,
                    timeout=timeout,
                    cookies=cookies,
                    proxies=proxies,
                    allow_redirects=allow_redirects,
                    verify=False
                )
            else:
                resp = requests.post(
                    url=url,
                    data=data,
                    headers=headers,
                    timeout=timeout,
                    cookies=cookies,
                    proxies=proxies,
                    allow_redirects=allow_redirects,
                    verify=False
                )

            if resp.status_code in allow_status:
                if not encoding:
                    resp.encoding = cchardet.detect(resp.content)[u'encoding']
                else:
                    resp.encoding = encoding
                resp_text = resp.text
                resp_headers = resp.headers
                resp_cookies = resp.cookies.get_dict()
                if cookies is not None:
                    cookies.update(resp_cookies)
                err_count = err_retry
            else:
                raise HTTPError(u'Invalid status code --> {0}\r\n{1}'.format(resp.status_code, resp.text))
        except Exception as e:
            logging.exception(u'Do http post({0}) error! - {1}'.format(url, e.message))
            if u'429' in repr(e):
                logging.debug(u'Too many requests in current proxy tunnel, sleep for a while...')
                err_count -= 1
            gevent.sleep(3)
        finally:
            if resp:
                try:
                    resp.close()
                except Exception as e:
                    logging.exception(u'failed to close post response! - {0}'.format(e.message))
        err_count += 1
    return resp_text, resp_headers, resp_cookies


def download(url, params=None, path=None, headers=None, timeout=20, cookies=None, proxies=False, allow_status=None,
             err_retry=3, allow_redirects=False):
    """
    下载文件
    :param url: 链接
    :param params: 请求参数
    :param path: 文件路径
    :param headers: 请求头
    :param timeout: timeout时间
    :param cookies: cookies
    :param proxies: 代理
    :param allow_status: 允许通过的状态码
    :param err_retry: 失败重试次数
    :param allow_redirects: 重定向参数
    :return: 文件流 | 响应头 | 响应的cookie
    """
    resp_buffer = resp_base64 = resp_headers = resp_cookies = None

    # 准备请求参数
    if not headers:
        headers = {u'User-Agent': random.choice(_BROWSER_HEADERS)}
    if not headers.get(u'User-Agent'):
        headers[u'User-Agent'] = random.choice(_BROWSER_HEADERS)
    headers = copy.deepcopy(headers)
    headers[u'User-Agent'] += u' {0}'.format(tools.random_char_num(int(tools.random_num(1))))
    if not allow_status:
        allow_status = [200]

    err_count = 0
    resp = None
    while err_count < err_retry:
        try:
            resp = requests.get(
                url=url,
                params=params,
                headers=headers,
                timeout=timeout,
                cookies=cookies,
                proxies=proxies,
                allow_redirects=allow_redirects,
                verify=False
            )
            if resp.status_code in allow_status:
                resp_buffer = resp.content
                resp.encoding = cchardet.detect(resp_buffer)[u'encoding']
                resp_base64 = base64.b64encode(resp_buffer)
                resp_headers = resp.headers
                resp_cookies = resp.cookies.get_dict()
                if cookies is not None:
                    cookies.update(resp_cookies)
                # 存储到指定位置
                if path:
                    with open(path, 'wb') as f:
                        for chunk in resp.iter_content():
                            if chunk:
                                f.write(chunk)
                                f.flush()
                err_count = err_retry
            else:
                raise HTTPError(u'Invalid status code --> {0}\r\n{1}'.format(resp.status_code, resp.text))
        except Exception as e:
            logging.exception(u'Do http get({0}) error! - {1}'.format(url, e.message))
            if u'429' in repr(e):
                logging.debug(u'Too many requests in current proxy tunnel, sleep for a while...')
                err_count -= 1
            gevent.sleep(3)
        finally:
            if resp:
                try:
                    resp.close()
                except Exception as e:
                    logging.exception(u'failed to close get response! - {0}'.format(e.message))
        err_count += 1
    return resp_buffer, resp_base64, resp_headers, resp_cookies
