# -*- coding: utf-8 -*-
import copy
import datetime
import io
import json
import logging
import os
import sys
import time

import gevent
from bson import ObjectId

from src.config import SOURCE_QUEUE_MAX_SIZE, CACHE_FILE_KEY
from src.cores.customer import CustomerJsonEncoder
from src.cores.services import excel_client
from src.cores.services import kafka_client
from src.cores.services.mongodb_client import MongodbClient
from src.cores.services.mongodb_client import MongodbService
from src.cores.services.mysql_client import MySQLClient
from src.cores.services.mysql_client import MySQLInterface
from src.setting import PROJECT_SETTING
from src.utils import tools


class SourceProvider(object):
    """消息Provider"""

    # 本地消息类型列表
    _localhost_message_types = [u'static', u'excel', u'csv', u'txt', u'daily']

    @classmethod
    def __load_cache_files(cls, params):
        """
        加载缓存消息文件
        :param params: 参数
        :return: 消息列表
        """
        messages = []
        plugin_id = tools.build_plugin_id(params)
        filename_list = [filename for filename in tools.list_folder_files(u'cache')
                         if plugin_id in filename and u'.' not in filename]
        for name in filename_list:
            try:
                message = tools.pickle_read_file(name)
                if message:
                    messages.append(message)
            except Exception as e:
                logging.exception(u'load cache files error! - {0}'.format(e.message))
            tools.remove_file(name)
        return messages

    @classmethod
    def __get_message_book_from_kafka(cls, params):
        """
        从kafka队列获取消息
        :param params: 参数
        :return: 获取的消息
        """
        message_book = None
        resp_text = kafka_client.poll(params[u'kafka_topic'], params[u'kafka_group'])
        if resp_text:
            try:
                message_book = json.loads(resp_text)
            except Exception as e:
                logging.exception(u'====>{0}<==== {1}'.format(resp_text, e.message))
                message_book = eval(resp_text)
        else:
            logging.debug(u'No records in kafka queue({0})!'.format(params[u'kafka_group']))
            gevent.sleep(1)
        return message_book

    @classmethod
    def __build_mongodb_query(cls, id_cache_file, params):
        """
        构造mongodb查询语句
        :param id_cache_file: id缓存文件
        :param params: 参数
        :return: 查询语句
        """
        query_dict = dict()
        if os.path.exists(id_cache_file):
            cache_id = tools.pickle_read_file(id_cache_file)
            if cache_id:
                if params[u'db_service']:
                    query_dict[u'_id'] = {u'$gt': {u'$oid': cache_id}}
                else:
                    query_dict[u'_id'] = {u'$gt': ObjectId(cache_id)}
        return query_dict

    @classmethod
    def __fill_mongodb_message_book(cls, params, message_book, msg):
        """
        按照配置中的键值列表筛选数据，并填充数据列表
        :param params: 参数
        :param message_book: 数据列表
        :param msg: 单条mongodb数据
        :return: 无
        """
        message = dict()
        for key in params[u'db_keys']:
            if key in msg.keys():
                if key == u'_id':
                    if params[u'db_service']:
                        message[key] = tools.clean_mongodb_service_id(msg[key])
                    else:
                        message[key] = str(msg[key])
                else:
                    message[key] = msg[key]
        if message:
            message_book.append(message)

    @classmethod
    def __get_message_book_from_mongodb(cls, params):
        """
        从mongodb获取数据
        :param params: 参数
        :return: 获取的消息
        """
        message_book = []
        id_cache_file = u'cache/{0}.id'.format(
            u'_'.join([u'mongodb', params[u'db_schema'], params[u'db_table'], tools.md5(params[u'class'])])
        )
        query_dict = cls.__build_mongodb_query(id_cache_file, params)
        db_records = []
        if params[u'db_service']:   # 使用接口服务
            records = MongodbService.find(
                params[u'db_schema'], params[u'db_table'], query_dict, params[u'db_limit'],
                env_schema=params.get(u'db_service_env')
            )
            if records:
                db_records = json.loads(records)
        else:                       # 直接连接数据库
            db_records = MongodbClient.find(params[u'db_schema'], params[u'db_table'], query_dict, params[u'db_limit'])

        if db_records:
            is_valid = False
            mongodb_id = None
            for msg in db_records:
                if msg:
                    if not is_valid:
                        is_valid = True
                    if params[u'db_service']:
                        mongodb_id = tools.clean_mongodb_service_id(msg[u'_id'])
                    else:
                        mongodb_id = str(msg[u'_id'])
                    cls.__fill_mongodb_message_book(params, message_book, msg)
            if is_valid and mongodb_id:
                logging.debug(u'{0}\'s object_id: {1}'.format(params[u'db_table'], mongodb_id))
                tools.pickle_write_file(id_cache_file, mongodb_id)
            else:
                logging.warning(u'++++++++> There\'re no records in mongodb({0})'.format(params[u'db_table']))
                if params.get(u'loop'):
                    tools.remove_file(id_cache_file)
        else:
            logging.warning(u'invalid mongodb records - {0}|query_dict:{1}'.format(db_records, query_dict))
            if params.get(u'loop'):
                tools.remove_file(id_cache_file)
            gevent.sleep(3)
        return message_book

    @classmethod
    def __build_mysql_filter_by_param(cls, filter_str, schema, key, value):
        """
        构造mysql查询的筛选参数
        :param filter_str: 筛选语句
        :param schema: 模式
        :param key: 键
        :param value: 值
        :return: 新的查询语句
        """
        if sys.version_info < (3, 4):
            type_value = eval('(str, unicode)')
        else:
            type_value = eval('str')
        if isinstance(value, type_value):
            if filter_str:
                filter_str += u' AND {0}'.format(u"{0}{1}'{2}'".format(key, schema, value))
            else:
                filter_str = u"{0}{1}'{2}'".format(key, schema, value)
        else:
            if filter_str:
                filter_str += u' AND {0}'.format(u'{0}{1}{2}'.format(key, schema, value))
            else:
                filter_str = u'{0}{1}{2}'.format(key, schema, value)
        return filter_str

    @classmethod
    def __build_mysql_query(cls, id_cache_file, params):
        """
        构造MySQL查询语句
        :param id_cache_file: id缓存文件
        :param params: 参数
        :return: 查询语句
        """
        query_str = u'SELECT {0} FROM {1}'.format(u','.join(params[u'db_keys']), params[u'db_table'])
        # 将缓存的id添加到筛选参数中
        if os.path.exists(id_cache_file):
            cache_id = tools.pickle_read_file(id_cache_file)
            if cache_id:
                if not params.get(u'db_filter'):
                    params[u'db_filter'] = dict()
                if not params[u'db_filter'].get(u'$gt'):
                    params[u'db_filter'][u'$gt'] = dict()
                params[u'db_filter'][u'$gt'][u'id'] = cache_id
        # 根据配置中的筛选参数查询
        filter_str = u''
        if params.get(u'db_filter'):
            # 等于
            if params[u'db_filter'].get(u'$e'):
                for key in params[u'db_filter'][u'$e'].keys():
                    filter_str = cls.__build_mysql_filter_by_param(
                        filter_str, u'=', key, params[u'db_filter'][u'$e'][key])
            # 不等于
            if params[u'db_filter'].get(u'$ne'):
                for key in params[u'db_filter'][u'$ne'].keys():
                    filter_str = cls.__build_mysql_filter_by_param(
                        filter_str, u'!=', key, params[u'db_filter'][u'$ne'][key])
            # 小于
            if params[u'db_filter'].get(u'$lt'):
                for key in params[u'db_filter'][u'$lt'].keys():
                    filter_str = cls.__build_mysql_filter_by_param(
                        filter_str, u'<', key, params[u'db_filter'][u'$lt'][key])
            # 小于等于
            if params[u'db_filter'].get(u'$lte'):
                for key in params[u'db_filter'][u'$lte'].keys():
                    filter_str = cls.__build_mysql_filter_by_param(
                        filter_str, u'<=', key, params[u'db_filter'][u'$lte'][key])
            # 大于
            if params[u'db_filter'].get(u'$gt'):
                for key in params[u'db_filter'][u'$gt'].keys():
                    filter_str = cls.__build_mysql_filter_by_param(
                        filter_str, u'>', key, params[u'db_filter'][u'$gt'][key])
            # 大于等于
            if params[u'db_filter'].get(u'$gte'):
                for key in params[u'db_filter'][u'$gte'].keys():
                    filter_str = cls.__build_mysql_filter_by_param(
                        filter_str, u'>=', key, params[u'db_filter'][u'$gte'][key])
        if filter_str:
            query_str += u' WHERE {0}'.format(filter_str)
        if params[u'db_limit'] is not None:
            query_str += u' LIMIT {0}'.format(params[u'db_limit'])
        return query_str

    @classmethod
    def __fill_mysql_message_book(cls, params, message_book, msg):
        """
        筛选数据，填充数据列表
        :param params: 参数
        :param message_book: 数据列表
        :param msg: 单条mysql数据
        :return: 无
        """
        message = dict()
        if params[u'db_service']:
            for key in msg:
                if isinstance(msg[key], dict) and u'$date' in msg[key].keys():
                    message[key] = time.strftime(u'%Y-%m-%d %H:%M:%S', time.localtime(msg[key][u'$date'] / 1000))
                else:
                    message[key] = msg[key]
        else:
            for i, key in enumerate(params[u'db_keys']):
                if isinstance(msg[i], datetime.datetime):
                    message[key] = msg[i].strftime(u'%Y-%m-%d %H:%M:%S')
                elif isinstance(msg[i], datetime.date):
                    message[key] = msg[i].strftime(u'%Y-%m-%d')
                else:
                    message[key] = msg[i]
        if message:
            message_book.append(message)

    @classmethod
    def __get_message_book_from_mysql(cls, params):
        """
        从MySQL获取数据
        :param params: 参数
        :return: 获取的消息
        """
        message_book = []
        if u'id' not in params[u'db_keys']:
            params[u'db_keys'].insert(0, u'id')

        id_cache_file = u'cache/{0}.id'.format(
            u'_'.join([u'mysql', params[u'db_schema'], params[u'db_table'], tools.md5(params[u'class'])])
        )
        query_str = cls.__build_mysql_query(id_cache_file, params)
        if params[u'db_service']:  # 使用接口服务
            db_records = MySQLInterface.find(
                schema=params[u'db_schema'],
                db_query=query_str,
                env_schema=params.get(u'db_service_env')
            )
        else:  # 直接连接数据库
            db_records = MySQLClient.find(params[u'db_schema'], query_str)

        if db_records:
            is_valid = False
            mysql_id = None
            for msg in db_records:
                if msg:
                    if not is_valid:
                        is_valid = True
                    if params[u'db_service']:
                        mysql_id = msg[u'id']
                    else:
                        mysql_id = msg[params[u'db_keys'].index(u'id')]
                    cls.__fill_mysql_message_book(params, message_book, msg)
            if is_valid and mysql_id:
                logging.debug(u'{0}\'s id: {1}'.format(params[u'db_table'], mysql_id))
                tools.pickle_write_file(id_cache_file, mysql_id)
            else:
                logging.warning(u'++++++++> There\'re no records in mysql({0})'.format(params[u'db_table']))
                if params.get(u'loop'):
                    tools.remove_file(id_cache_file)
        else:
            logging.warning(u'invalid mysql records - {0}|query_str:{1}'.format(db_records, query_str))
            if params.get(u'loop'):
                tools.remove_file(id_cache_file)
            gevent.sleep(3)
        return message_book

    @classmethod
    def __read_record_from_excel(cls, filename, workbook, sheet_names, source_queue, params, mark_num, mark_file):
        """
        从excel文件读取数据
        :param filename: excel文件名
        :param workbook: excel文件对象
        :param sheet_names: sheet名列表
        :param source_queue: 消息队列
        :param params: 配置参数
        :param mark_num: 记录在临时文件中的已经读取到的行数
        :param mark_file: 记录行数的临时文件名
        :return: 无
        """
        sheet, row_num, col_num = excel_client.read_sheet_by_name(workbook, sheet_names[0])
        for i in tools.irange(0, row_num):
            if i <= mark_num:
                continue
            record = excel_client.read_sheet_row_by_index(sheet, i)
            if record:
                message = dict()
                for index, value in enumerate(record):
                    message[u'key{0}'.format(index)] = value
                # message_book.append(message)
                while 1:
                    if source_queue.qsize() < SOURCE_QUEUE_MAX_SIZE:
                        cls.__source_queue_pusher(source_queue, params, message)
                        if i % 100 == 0:
                            logging.info(u'========> {0}-{1}已经发送了{2}条数据'.format(
                                params.get(u'province', u'Provider'), filename, i + 1))
                        if i % 1000 == 0:
                            tools.pickle_write_file(mark_file, max(0, i - 1000))
                            gevent.sleep(0.1)
                        break
                    else:
                        tools.pickle_write_file(mark_file, max(i - 1000, tools.pickle_read_file(mark_file)))
                        gevent.sleep(2)
        # 遍历完毕，设置mark_file为-1
        tools.pickle_write_file(mark_file, -1)

    @classmethod
    def __get_message_book_from_excel(cls, source_queue, params):
        """
        从excel获取数据
        :param source_queue: 消息队列
        :param params: 参数
        :return: 获取的消息
        """
        message_book = []
        try:
            for filename in params[u'messages']:
                if os.path.exists(filename):
                    workbook, sheet_names = excel_client.read_excel(filename)
                    if sheet_names:
                        mark_file = cls.__init_mark_file_name(params, filename)
                        mark_num = cls.__init_mark_num(mark_file)
                        if mark_num == -1:
                            logging.warning(u'========> {0} has been finished!'.format(filename))
                            continue
                        cls.__read_record_from_excel(
                            filename, workbook, sheet_names, source_queue, params, mark_num, mark_file)
        except Exception as e:
            logging.exception(u'Get messages from excel error! - {0}'.format(e.message))
        return message_book

    @classmethod
    def __read_record_from_csv(cls, filename, source_encode, source_queue, params, mark_num, mark_file):
        """
        从csv文件读取数据
        :param filename: 文件名
        :param source_encode: 文件编码
        :param source_queue: 消息队列
        :param params: 配置参数
        :param mark_num: 记录在临时文件中的已经读取到的行数
        :param mark_num: 记录行数的临时文件名
        :return: 无
        """
        count = 0
        with io.open(filename, encoding=source_encode) as f:
            try:
                for line in f:
                    count += 1
                    if count <= mark_num:
                        continue
                    row_items = line.split(u',')
                    if row_items:
                        message = dict()
                        for index, value in enumerate(row_items):
                            message[u'key{0}'.format(index)] = value.strip()
                        # message_book.append(message)
                        while 1:
                            if source_queue.qsize() < SOURCE_QUEUE_MAX_SIZE:
                                cls.__source_queue_pusher(source_queue, params, message)
                                if count % 100 == 0:
                                    logging.info(u'========> {0}-{1}已经发送了{2}条数据'.format(
                                        params.get(u'province', u'Provider'), filename, count))
                                if count % 1000 == 0:
                                    tools.pickle_write_file(mark_file, max(0, count - 1000))
                                    gevent.sleep(0.1)
                                break
                            else:
                                tools.pickle_write_file(mark_file, max(count - 1000, tools.pickle_read_file(mark_file)))
                                gevent.sleep(2)
                # 遍历完毕，设置mark_file为-1
                tools.pickle_write_file(mark_file, -1)
            except Exception as e:
                logging.exception(u'Read CSV file Error! - {0}'.format(e.message))

    @classmethod
    def __get_message_book_from_csv(cls, source_queue, params):
        """
        从CSV获取数据
        :param source_queue: 消息队列
        :param params: 参数
        :return: 获取的消息
        """
        message_book = []
        try:
            source_encode = u'UTF-8'
            if params.get(u'source_encode'):
                source_encode = params[u'source_encode']
            for filename in params[u'messages']:
                if os.path.exists(filename):
                    mark_file = cls.__init_mark_file_name(params, filename)
                    mark_num = cls.__init_mark_num(mark_file)
                    if mark_num == -1:
                        logging.warning(u'========> {0} has been finished!'.format(filename))
                        continue
                    cls.__read_record_from_csv(filename, source_encode, source_queue, params, mark_num, mark_file)
        except Exception as e:
            logging.exception(u'Get message from csv error! - {0}'.format(e.message))
        return message_book

    @staticmethod
    def __init_mark_file_name(params, filename):
        """
        初始化记录文件名
        :param params: 配置参数
        :param filename: 数据源文件
        :return: 记录文件名
        """
        return u'cache/{0}_num_{1}_{2}.txt'.format(
                    params[u'source'], filename.split(u'/')[-1].split(u'.')[0], tools.build_plugin_id(params))

    @staticmethod
    def __init_mark_num(mark_file):
        """
        初始化记录
        :param mark_file: 记录文件名
        :return: 记录
        """
        mark_num = 0
        if os.path.exists(mark_file):
            mark_num = tools.pickle_read_file(mark_file)
        return mark_num

    @classmethod
    def __get_message_book(cls, source_queue, params, first):
        """
        获取消息数据
        :param params: 参数
        :param first: first标签
        :return: 获取的消息
        """
        message_book = None
        try:
            if first:
                message_book = cls.__load_cache_files(params)
            else:
                if params[u'source'] in [u'static']:
                    message_book = copy.deepcopy(params[u'messages'])
                elif params[u'source'] in [u'excel']:
                    message_book = cls.__get_message_book_from_excel(source_queue, params)
                elif params[u'source'] in [u'csv', u'txt']:
                    message_book = cls.__get_message_book_from_csv(source_queue, params)
                elif params[u'source'] == u'daily':
                    message_book = [{u'date': tools.days_before(1)}]
                else:
                    if params[u'source'] == u'kafka':
                        message_book = cls.__get_message_book_from_kafka(params)
                    elif params[u'source'] == u'mongodb':
                        message_book = cls.__get_message_book_from_mongodb(params)
                    elif params[u'source'] == u'mysql':
                        message_book = cls.__get_message_book_from_mysql(params)
        except Exception as e:
            logging.exception(u'get message error! - {0}'.format(e.message))
            gevent.sleep(10)
        return message_book

    @classmethod
    def __cache_message_pickle(cls, params, message):
        """
        将消息缓存至临时文件
        :param params: 参数
        :param message: 消息主体
        :return: 无
        """
        filename = u'cache/{0}_{1}'.format(tools.build_plugin_id(params), tools.build_plugin_id(message))
        try:
            tools.pickle_write_file(filename, message)
            message[CACHE_FILE_KEY] = filename
        except Exception as e:
            logging.exception(u'cache message pickle error! - {0}'.format(e.message))

    @classmethod
    def __source_queue_pusher(cls, source_queue, params, message):
        """
        将消息发送到消息队列
        :param source_queue: 消息队列
        :param params: 参数
        :param message: 消息
        :return: 无
        """
        if not isinstance(message, dict):
            logging.error(u'Invalid message! - {0}'.format(message))
            return
        # 缓存至临时文件
        # 从本地消息中加载的数据不写入文件
        if params[u'source'] not in cls._localhost_message_types:
            cls.__cache_message_pickle(params, message)
        # 将消息发送到内存队列
        source_queue.put((
            int(params[u'priority']),
            json.dumps({u'message': message, u'config': params}, ensure_ascii=False, cls=CustomerJsonEncoder)
        ))

    @classmethod
    def __push_source_messages(cls, source_queue, params, first):
        """
        获取数据并将数据发送到消息队列
        :param source_queue: 消息队列
        :param params: 配置参数
        :param first: first标签
        :return:
        """
        message_book = cls.__get_message_book(source_queue, params, first)
        if message_book:
            if isinstance(message_book, dict):
                cls.__source_queue_pusher(source_queue, params, message_book)
            elif isinstance(message_book, list):
                for m in message_book:
                    cls.__source_queue_pusher(source_queue, params, m)
            else:
                raise TypeError(u'Invalid message type! - {0}'.format(message_book))

    @classmethod
    def run(cls, args):
        """
        提供单个插件的消息
        :param args: 参数
        :return: 无
        """
        params, source_queue = args
        first = True
        while 1:
            try:
                # 检查运行时间
                tools.check_run_time(params)
                logging.debug(u'There\'re {0} messages in source queue.'.format(source_queue.qsize()))
                if params[u'source'] in cls._localhost_message_types:
                    SourceProvider.__push_source_messages(source_queue, params, first)
                    if first:
                        first = False
                    else:
                        logging.warning(u'++++++++++++++++++> source provider end!')
                        gevent.sleep(60)
                        if not params.get(u'loop'):
                            break
                elif source_queue.qsize() < SOURCE_QUEUE_MAX_SIZE:
                    SourceProvider.__push_source_messages(source_queue, params, first)
                    if first:
                        first = False
                else:
                    logging.debug(u'too many messages in source queue!')
                    gevent.sleep(10)
            except Exception as e:
                logging.exception(u'source provider error! - {0}'.format(e.message))
                gevent.sleep(3)


def run(args):
    """
    开启所有插件的消息提供
    :param args: 参数
    :return: 无
    """
    options, source_queue = args
    tasks = list()
    for plugin in PROJECT_SETTING[u'PLUGINS'][options.schema]:
        plugin_set = copy.deepcopy(PROJECT_SETTING[u'COMMON'])
        plugin_set.update(plugin)
        tasks.append(gevent.spawn(SourceProvider.run, (plugin_set, source_queue)))
    gevent.joinall(tasks)
