# -*- coding: utf-8 -*-
import importlib
import json
import logging

import gevent

from src.config import CACHE_FILE_KEY
from src.cores.customer import CustomerJsonEncoder
from baseitem import BaseItem
from src.cores.pipeline import result_pusher, Pipeline
from src.cores.services.proxy_client import ProxyService
from src.utils import tools


class Processor(object):
    """处理函数父类"""

    def __init__(self, config, source_queue, result_queue):
        """
        初始化处理函数实例
        :param config: 配置参数
        :param source_queue: 消息队列
        :param result_queue: 结果队列
        """
        self.config = config
        self.source_queue = source_queue
        self.result_queue = result_queue
        self.retry_limit = 10
        self.timeout = 20
        self.base_headers = {
            u'User-Agent': u'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
            u'Accept': u'*/*',
            u'Accept-Language': u'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            u'Accept-Encoding': u'gzip, deflate',
            u'Connection': u'keep-alive'
        }
        self.base_cookies = dict()
        self.base_proxies = None
        self.breakpoint = False

    def refresh_proxy(self, dynamic=False, change=True):
        """
        刷新代理
        :param dynamic: 是否使用动态代理
        :param change: 是否更新现有代理
        :return: 无
        """
        if not self.base_proxies:
            self.base_proxies = ProxyService.get_proxy() if not dynamic else ProxyService.get_dynamic_proxy()
        else:
            if not dynamic:
                if change:
                    while 1:
                        temp = ProxyService.get_proxy()
                        if temp != self.base_proxies:
                            self.base_proxies = temp
                            break
                else:
                    pass
            else:
                self.base_proxies = ProxyService.get_dynamic_proxy()

    @staticmethod
    def build_ent_eid_by_name(name):
        """
        根据企业名称查询企业eid
        :param name: 企业名
        :return: 企业eid
        """
        return Pipeline.build_ent_eid_by_name(name)

    @staticmethod
    def remove_cache_file(message):
        """
        移除缓存文件
        :param message: 消息主体
        :return: 无
        """
        # 删除缓存文件
        try:
            file_path = message.get(CACHE_FILE_KEY)
            if file_path:
                tools.remove_file(file_path)
                logging.debug(u'remove cache file({0}) successfully!'.format(file_path))
        except Exception as e:
            logging.exception(u'failed to remove cache file! - {0}'.format(e.message))

    def pipeline_pusher(self, message, record, record_cls):
        """
        将结果发送到处理管道
        :param message: 消息对象
        :param record: 结果对象
        :param record_cls: 结果类
        :return: 无
        """
        result_pusher(record, self.config, self.result_queue, message, record_cls)

    def source_queue_pusher(self, new_message):
        """
        将新的消息发送到消息队列
        :param new_message: 新的消息
        :return:
        """
        if not isinstance(new_message, dict):
            logging.error(u'Invalid message! - {0}'.format(new_message))
            return
        if CACHE_FILE_KEY in new_message.keys():
            new_message.pop(CACHE_FILE_KEY)
        # 将消息缓存至临时文件
        filename = u'cache/{0}_{1}'.format(tools.build_plugin_id(self.config), tools.build_plugin_id(new_message))
        try:
            tools.pickle_write_file(filename, new_message)
            new_message[CACHE_FILE_KEY] = filename
        except Exception as e:
            logging.exception(u'cache message pickle error! - {0}'.format(e.message))

        # 将消息发送到消息队列
        self.source_queue.put((
            int(self.config[u'priority']),
            json.dumps({u'message': new_message, u'config': self.config}, ensure_ascii=False, cls=CustomerJsonEncoder)
        ))

    def request_list_page(self, message, page_no):
        """
        请求列表页数据
        :param message: 原始消息
        :param page_no: 当前页码
        :return: 最大页码 | 列表页数据集合 | 结果类 | 是否有详情页
        """
        max_page_no = 1
        list_records = []
        has_detail = False
        item = BaseItem()

        list_records.append(item)
        logging.debug(message)
        logging.debug(self.config)
        return max_page_no, list_records, BaseItem, has_detail

    def request_detail_page(self, message, record, record_cls):
        """
        请求详情页
        :param message: 消息主体
        :param record: 抓取到的列表页信息
        :param record_cls: 列表页信息结果类
        :return: 无
        """
        self.pipeline_pusher(message, record, record_cls)

    def __request_detail(self, args):
        """
        请求详情页入口函数
        :param args: 参数的集合
        :return: 无
        """
        message, record, record_cls = args
        self.request_detail_page(message, record, record_cls)

    def run(self, message):
        """
        处理函数开始方法
        :param message: 消息主体
        :return: 无
        """
        current_page_no = max_page_no = 1
        self.breakpoint = False
        while current_page_no <= max_page_no:
            try:
                logging.debug(u'====> {0} - Starting page {1}/{2} of {3}'.format(
                    self.__class__.__name__, current_page_no, max_page_no, json.dumps(message, ensure_ascii=False)))
                temp_max_page_no, list_records, record_cls, has_detail = self.request_list_page(
                    message, current_page_no)
                max_page_no = max(max_page_no, temp_max_page_no)
                if not list_records:
                    logging.debug(u'{0} has no list_records!'.format(json.dumps(message, ensure_ascii=False)))
                    self.remove_cache_file(message)
                else:
                    if not has_detail:
                        for record in list_records:
                            self.pipeline_pusher(message, record, record_cls)
                    else:
                        tasks = []
                        for record in list_records:
                            tasks.append(gevent.spawn(self.__request_detail, (message, record, record_cls)))
                        gevent.joinall(tasks)
                logging.debug(u'====> {0} - The end of page {1}/{2} of {3}'.format(
                    self.__class__.__name__, current_page_no, max_page_no, json.dumps(message, ensure_ascii=False)))
                current_page_no += 1
            except Exception as e:
                logging.exception(e.message)
                self.remove_cache_file(message)

            if self.breakpoint:
                logging.warning(u'====> Capture the breakpoint signal~')
                break


def __springboard(args):
    """
    跳板函数
    :param args: 参数
    :return: 无
    """
    source_queue, result_queue = args
    instance_dic = dict()
    while 1:
        try:
            if not source_queue.empty():
                priority, temp_args = source_queue.get()
                args = json.loads(temp_args)
                config = args[u'config']
                config_id = tools.build_plugin_id(config)
                if config_id not in instance_dic.keys():
                    # 动态加载模块
                    name = config[u'class'].split(u'.')[-1]
                    i_module = importlib.import_module(config[u'class'], name)
                    cls = getattr(i_module, name)
                    instance_dic[config_id] = cls(config, source_queue, result_queue)
                instance_dic[config_id].run(args[u'message'])
            else:
                gevent.sleep(10)
        except Exception as e:
            logging.exception(u'springboard error! - {0}'.format(e.message))
            gevent.sleep(2)


def run(args):
    """
    主处理函数
    :param args: 参数
    :return: 无
    """
    options, source_queue, result_queue = args
    tasks = list()
    for i in range(options.task):
        tasks.append(gevent.spawn(__springboard, (source_queue, result_queue)))
    gevent.joinall(tasks)
