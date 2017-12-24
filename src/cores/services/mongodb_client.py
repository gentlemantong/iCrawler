# -*- coding: utf-8 -*-
import copy
import json

import pymongo
from pymongo.errors import *

from src.config import ENVIRONMENT, MONGODB_CONFIG
from src.cores.customer import CustomerJsonEncoder
from src.cores.services import http_client


class MongodbClient(object):
    """mongodb client 方法类"""

    _CLIENTS = dict()
    _DBS = dict()

    @classmethod
    def __init_client(cls, schema):
        """
        初始化mongodb client
        :param schema: 模式名
        :return: 无
        """
        if schema not in cls._DBS.keys():
            config = MONGODB_CONFIG[schema]
            # 建立数据库连接
            client = pymongo.MongoClient(
                host=config[u'host'],
                port=config[u'port']
            )
            db = client[config[u'db']]

            # 验证
            if config[u'name'] and config[u'password']:
                auth_result = db.authenticate(name=config[u'name'], password=config[u'password'])
            else:
                auth_result = True

            # 添加到类的变量集合中
            if auth_result:
                cls._CLIENTS[schema] = client
                cls._DBS[schema] = db
            else:
                raise ConfigurationError(u'[mongodb]auth failed!')

    @classmethod
    def __get_table(cls, schema, table):
        """
        获取表链接对象
        :param schema: 模式名
        :param table: 表名
        :return: 表连接对象
        """
        cls.__init_client(schema)
        return cls._DBS[schema][table]

    @classmethod
    def __close_conn(cls, schema=None):
        """
        关闭指定模式的连接
        :param schema: 模式名，默认关闭所有模式的连接
        :return: 无
        """
        if schema is None:
            keys = copy.deepcopy(list(cls._CLIENTS.keys()))
            for key in keys:
                cls.__close_conn(schema=key)
        else:
            if schema in cls._CLIENTS.keys():
                cls._CLIENTS[schema].close()
                cls._CLIENTS.pop(schema)
                cls._DBS.pop(schema)

    @classmethod
    def reconnect(cls, schema):
        """
        重连指定模式的连接
        :param schema: 模式名
        :return: 无
        """
        cls.__close_conn(schema)
        cls.__init_client(schema)

    @classmethod
    def update_one(cls, schema, table, query_dict, update_dict, upsert=False):
        """
        更新指定的一跳数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param update_dict: 更新语句
        :param upsert: 若数据库中不存在该数据，是否新增
        :return: 操作结果
        """
        db = cls.__get_table(schema, table)
        if not db:
            raise CursorNotFound(u'[mongodb]table not found!')

        # 检查更新语句有效性
        if not isinstance(update_dict, dict) or not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')
        for key in [u'$set', u'$addToSet', u'$setOnInsert', u'$inc']:
            if key in update_dict.keys():
                break
        else:
            raise CollectionInvalid(u'[mongodb]not a valid update record!')

        update_result = db.update_one(query_dict, update_dict, upsert)
        return update_result

    @classmethod
    def find(cls, schema, table, query_dict, limit=None):
        """
        查询符合条件的多条数据。若limit不赋值，则返回所有符合条件的数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param limit: 最大返回数量
        :return: 查询结果
        """
        db = cls.__get_table(schema, table)
        if not db:
            raise CursorNotFound(u'[mongodb]table not found!')

        # 检查查询语句有效性
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        if limit:
            results = db.find(query_dict, sort=[(u'_id', pymongo.ASCENDING)], limit=limit)
        else:
            results = db.find(query_dict, sort=[(u'_id', pymongo.ASCENDING)])
        return results

    @classmethod
    def find_one(cls, schema, table, query_dict):
        """
        查询符合条件的一条数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :return: 查询结果
        """
        db = cls.__get_table(schema, table)
        if not db:
            raise CursorNotFound(u'[mongodb]table not found!')

        # 检查查询语句有效性
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')
        return db.find_one(query_dict)

    @classmethod
    def delete_one(cls, schema, table, query_dict):
        """
        删除一跳数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :return: 操作结果
        """
        db = cls.__get_table(schema, table)
        if not db:
            raise CursorNotFound(u'[mongodb]table not found!')

        # 检查查询语句有效性
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')
        return db.delete_one(query_dict)

    @classmethod
    def insert_one(cls, schema, table, update_dict):
        """
        直接插入一条数据
        :param schema: 模式名
        :param table: 表名
        :param update_dict: 需要插入的数据
        :return: 操作结果
        """
        db = cls.__get_table(schema, table)
        if not db:
            raise CursorNotFound(u'[mongodb]table not found!')

        # 检查查询语句有效性
        if not isinstance(update_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')
        return db.insert(update_dict)

    @classmethod
    def count(cls, schema, table, query_dict):
        """
        查询符合条件的数据数量
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :return: 数量
        """
        db = cls.__get_table(schema, table)
        if not db:
            raise CursorNotFound(u'[mongodb]table not found!')

        # 检查查询语句有效性
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')
        return db.count(query_dict)


class MongodbService(object):
    """二次封装的mongodb服务类"""

    @classmethod
    def find_one(cls, schema, table, query_dict, columns=None, env_schema=None):
        """
        查询符合条件的一条数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param columns: 过滤的字段，数组['field1', 'field2']
        :param env_schema: 环境模式
        :return: 查询结果
        """
        if not env_schema:
            env_schema = ENVIRONMENT
        url = u'http://{0}:{1}/mongo/find_one'.format(
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'host'],
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'port']
        )
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        query_str = json.dumps(query_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        data = {
            u'schema': schema,
            u'tablename': table,
            u'query_str': query_str
        }
        if columns:
            data['columns'] = json.dumps(columns)
        return (http_client.do_http_post(url, data=data))[0]

    @classmethod
    def find(cls, schema, table, query_dict, limit, columns=None, env_schema=None):
        """
        查询符合条件的多条数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param limit: 数据量
        :param env_schema: 环境模式
        :param columns: 过滤字段
        :return: 查询结果
        """
        if not env_schema:
            env_schema = ENVIRONMENT
        url = u'http://{0}:{1}/mongo/find'.format(
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'host'],
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'port']
        )
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        query_str = json.dumps(query_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        data = {
            u'schema': schema,
            u'tablename': table,
            u'query_str': query_str,
            u'limit': limit,
        }
        if columns:
            data[u"columns"] = json.dumps(columns)
        return (http_client.do_http_post(url, data=data))[0]

    @classmethod
    def insert_one(cls, schema, table, update_dict, env_schema=None):
        """
        直接插入一条数据
        :param schema: 模式名
        :param table: 表名
        :param update_dict: 需要插入的数据
        :param env_schema: 环境模式
        :return: 操作结果
        """
        if not env_schema:
            env_schema = ENVIRONMENT
        url = u'http://{0}:{1}/mongo/insert_one'.format(
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'host'],
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'port']
        )
        if not isinstance(update_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        update_str = json.dumps(update_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        data = {
            u'schema': schema,
            u'tablename': table,
            u'data_str': update_str
        }
        return (http_client.do_http_post(url, data=data))[0]

    @classmethod
    def update_one(cls, schema, table, query_dict, update_dict, upsert=False, env_schema=None):
        """
        更新一条数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param update_dict: 需要更新的数据
        :param upsert: 当数据库中不存在该条数据时，是否新增
        :param env_schema: 环境模式
        :return: 操作结果
        """
        if not env_schema:
            env_schema = ENVIRONMENT
        url = u'http://{0}:{1}/mongo/update_one'.format(
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'host'],
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'port']
        )
        if not isinstance(update_dict, dict) or not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        query_str = json.dumps(query_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        update_str = json.dumps(update_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        data = {
            u'schema': schema,
            u'tablename': table,
            u'query_str': query_str,
            u'data_str': update_str,
            u'upsert': str(upsert).lower()
        }
        return (http_client.do_http_post(url, data=data))[0]

    @classmethod
    def delete_one(cls, schema, table, query_dict, env_schema=None):
        """
        删除一条数据
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param env_schema: 环境模式
        :return: 操作结果
        """
        if not env_schema:
            env_schema = ENVIRONMENT
        url = u'http://{0}:{1}/mongo/delete_one'.format(
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'host'],
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'port']
        )
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        query_str = json.dumps(query_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        data = {
            u'schema': schema,
            u'tablename': table,
            u'query_str': query_str
        }
        return (http_client.do_http_post(url, data=data))[0]

    @classmethod
    def count(cls, schema, table, query_dict, env_schema=None):
        """
        获取符合条件的数据总量
        :param schema: 模式名
        :param table: 表名
        :param query_dict: 查询语句
        :param env_schema: 环境模式
        :return: 查询结果
        """
        if not env_schema:
            env_schema = ENVIRONMENT
        url = u'http://{0}:{1}/mongo/count'.format(
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'host'],
            MONGODB_CONFIG[u'SERVICE'][env_schema][u'port']
        )
        if not isinstance(query_dict, dict):
            raise CollectionInvalid(u'[mongodb]not a dict!')

        query_str = json.dumps(query_dict, ensure_ascii=False, cls=CustomerJsonEncoder)
        data = {
            u'schema': schema,
            u'tablename': table,
            u'query_str': query_str
        }
        return (http_client.do_http_post(url, data=data))[0]
