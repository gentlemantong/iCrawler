# -*- coding: utf-8 -*-
import json
import logging

from baseitem import BaseItem, Type

from src.config import DAMA_CONFIG, DAMA_NACAO_CONFIG, ENVIRONMENT
from src.cores.services import http_client
from src.cores.services.dama2_client import Dama2Client


class Captcha(BaseItem):
    """验证码结果类"""

    success = Type(data_type=bool)
    id = Type(data_type=str)
    value = Type(data_type=str)


class Dama(object):
    """打码服务"""

    @classmethod
    def sx_ocr(cls, img_base64):
        """
        被执行人、失信被执行人验证码
        :param img_base64: base64编码的图片
        :return: 打码结果
        """
        result = Captcha()
        url = u'http://{0}:{1}/sx_ocr/do'.format(DAMA_CONFIG[ENVIRONMENT][u'host'], DAMA_CONFIG[ENVIRONMENT][u'port'])
        resp_text = (http_client.do_http_post(
            url=url,
            data={u'img': img_base64}
        ))[0]
        if resp_text:
            logging.debug(resp_text)
            resp_json = json.loads(resp_text)
            if resp_json.get(u'success') == u'1':
                setattr(result, u'success', True)
                setattr(result, u'id', u'')
                setattr(result, u'value', resp_json[u'data'])
        return result

    @classmethod
    def nacao_ocr(cls, img_base64):
        """
        全国组织机构代码中心验证码
        :param img_base64: base64编码的图片
        :return: 打码结果
        """
        result = Captcha()
        url = u'http://{0}:{1}/sx_ocr/nacao'.format(
            DAMA_NACAO_CONFIG[ENVIRONMENT][u'host'], DAMA_NACAO_CONFIG[ENVIRONMENT][u'port'])
        resp_text = (http_client.do_http_post(
            url=url,
            data={u'img': img_base64},
            timeout=60
        ))[0]
        if resp_text:
            logging.debug(resp_text)
            resp_json = json.loads(resp_text)
            if resp_json.get(u'success') == u'1' and resp_json.get(u'data'):
                setattr(result, u'success', True)
                setattr(result, u'id', u'')
                setattr(result, u'value', resp_json[u'data'])
        return result

    @classmethod
    def base_ocr(cls, img_buffer):
        """
        基础验证码打码
        :param img_buffer: 图片流
        :return: 打码结果
        """
        result = Captcha()
        captcha = Dama2Client.decode_file_buffer(img_buffer)
        for key in captcha:
            setattr(result, key, captcha[key])
        return result

    @classmethod
    def report_error(cls, captcha):
        """
        上报打码错误
        :param captcha: 验证码结果
        :return: 无
        """
        ret = None
        if getattr(captcha, u'id', None):
            ret = Dama2Client.report_error(captcha.id)
        return ret
