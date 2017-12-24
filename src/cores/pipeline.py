# -*- coding: utf-8 -*-
import copy
import importlib
import json
import logging

import gevent

from src.config import RESULT_QUEUE_MAX_SIZE, CACHE_FILE_KEY
from src.cores.customer import CustomerJsonEncoder
from baseitem import dumps_item
from src.cores.services import kafka_client, ots_client
from src.cores.services.mongodb_client import MongodbService
from src.cores.services.oss_client import OSSService
from src.utils import tools


class Pipeline(object):
    """pipeline父类"""

    def __init__(self):
        pass

    @staticmethod
    def transfer_none_to_empty_str(record):
        """
        将结果中的None值转换为空字符串
        :param record: 结果
        :return: 无
        """
        for key in record.keys():
            if record[key] is None:
                record[key] = u''

    @staticmethod
    def build_ent_eid_by_name(name):
        """
        根据企业名称查询企业eid
        :param name: 企业名
        :return: 企业eid
        """
        eid = u''
        if name:
            resp_text = None
            try:
                query_dict = {u'name': name.replace(u'(', u'（').replace(u')', u'）')}
                resp_text = MongodbService.find_one(u'gs', u'entities', query_dict, [u'eid'])
                if resp_text:
                    eid = json.loads(resp_text)[u'eid']
            except Exception as e:
                logging.exception(u'{0} - {1}'.format(e.message, resp_text))
        return eid

    @staticmethod
    def flow_to_ots(instance, table, pk, columns):
        """
        流向OTS
        :param instance: OTS实例
        :param table: 表名
        :param pk: pk
        :param columns: 需要更新的列名
        :return: 操作结果
        """
        put_result = None
        if instance and table and pk and columns:
            put_result = ots_client.ots_service_put_row(instance, table, pk, columns)
            logging.debug(u'Finished putted record to OTS({0}-{1})!'.format(instance, table))
        else:
            logging.exception(u'Invalid OTS params! - instance({0}), table({1}), pk({2}), columns({3})'.format(
                instance, table, pk, columns))
        return put_result

    @staticmethod
    def flow_to_oss(bucket_name, folder_name, filename, record):
        """
        流向OSS
        :param bucket_name: 存储的bucket
        :param folder_name: 存储的文件夹
        :param filename: 存储的文件名
        :param record: 数据
        :return: 操作结果
        """
        put_result = None
        if record:
            put_result = OSSService.put_text(bucket_name, folder_name, filename, record)
            logging.debug(
                u'Finished putted record to OSS({0}.{1}.{2})!'.format(bucket_name, folder_name, filename))
        else:
            logging.exception(
                u'Invalid record for OSS({0}.{1}.{2})!'.format(bucket_name, folder_name, filename))
        return put_result

    @staticmethod
    def flow_to_kafka(kafka_topic, record):
        """
        流向kafka
        :param kafka_topic: kafka队列的topic
        :param record: 数据
        :return: 操作结果
        """
        put_result = None
        if record:
            put_result = kafka_client.offer(kafka_topic, record)
            logging.debug(u'Finished putted record to Kafka({0})!'.format(kafka_topic))
        else:
            logging.exception(u'Invalid record for Kafka({0})!'.format(kafka_topic))
        return put_result

    def flow_to_oss_and_kafka(self, bucket_name, folder_name, filename, oss_record, kafka_topic, kafka_record):
        """
        流向kafka和OSS
        :param bucket_name: oss的bucket
        :param folder_name: 指定bucket下的文件夹
        :param filename: oss文件名
        :param oss_record: 需要流向oss的数据
        :param kafka_topic: kafka的topic
        :param kafka_record: 需要流向kafka
        :return: 无
        """
        oss_put_result = self.flow_to_oss(bucket_name, folder_name, filename, oss_record)
        if oss_put_result:
            self.flow_to_kafka(kafka_topic, kafka_record)

    def process_item(self, config, result, message):
        """
        处理结果，将数据发往下一步进行处理
        :param config: 配置
        :param result: 处理后的消息对象
        :param message: 查询参数
        :return: 无
        """
        logging.debug(self.__class__.__name__)
        logging.debug(result)

    def run(self, args):
        """
        pipeline开始函数
        :param args: 结果参数
            {
                'result': '',  # 处理后的消息对象
                'config': '',  # 参数
                'message': ''  # 原始消息
            }
        :return:
        """
        result = copy.deepcopy(args[u'result'])
        config = copy.deepcopy(args[u'config'])
        message = copy.deepcopy(args[u'message'])

        # 处理结果，将数据发往下一步进行处理
        try:
            self.process_item(config, result, message)
        except Exception as e:
            logging.exception(e.message)

        # 删除缓存文件
        try:
            file_path = message.get(CACHE_FILE_KEY)
            if file_path:
                tools.remove_file(file_path)
                logging.debug(u'remove cache file({0}) successfully!'.format(file_path))
        except Exception as e:
            logging.exception(u'failed to remove cache file! - {0}'.format(e.message))


def result_pusher(record, config, result_queue, message, record_cls=None):
    """
    push record into result_queue
    :param record: 数据
    :param config: 配置
    :param result_queue: 结果队列
    :param message: 原始消息
    :param record_cls: 结果类
    :return: 无
    """
    while 1:
        try:
            if record_cls is not None and isinstance(record, record_cls):
                result = dict()
                if record.__slots__:
                    for key in record.__slots__:
                        result[key] = getattr(record, key, None)
                else:
                    result = dumps_item(record)
            else:
                result = copy.deepcopy(record)

            if result_queue.qsize() < RESULT_QUEUE_MAX_SIZE:
                result_queue.put((
                    int(config[u'priority']),
                    json.dumps(
                        {u'result': result, u'config': config, u'message': message},
                        ensure_ascii=False,
                        cls=CustomerJsonEncoder
                    )
                ))
                logging.debug(u'push {0} to result queue successfully!'.format(record_cls))
                break
            else:
                logging.debug(u'too many records in result queue!')
                gevent.sleep(10)
        except Exception as e:
            logging.exception(u'result pusher error! - {0}'.format(e.message))


def result_handler(result_queue):
    """
    result handler
    :param result_queue: 结果队列
    :return: 无
    """
    pipeline_dict = dict()
    while 1:
        try:
            if not result_queue.empty():
                priority, temp_args = result_queue.get()
                args = json.loads(temp_args)
                plugin_id = tools.build_plugin_id(args[u'config'])
                if plugin_id not in pipeline_dict.keys():
                    # 动态加载模块
                    name = args[u'config'][u'pipeline'].split(u'.')[-1]
                    i_module = importlib.import_module(args[u'config'][u'pipeline'], name)
                    cls = getattr(i_module, name)
                    pipeline_dict[plugin_id] = cls()
                pipeline_dict[plugin_id].run(args)
            else:
                gevent.sleep(10)
        except Exception as e:
            logging.exception(u'result handler error! - {0}'.format(e.message))
            gevent.sleep(3)
