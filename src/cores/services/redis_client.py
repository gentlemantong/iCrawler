# _*_ coding: utf-8 _*_
import copy
import logging
import threading

import datetime
import redis as redis

from src.config import REDIS_CONFIG, ENVIRONMENT


class RedisClient(object):
    """
    Redis Client
    """
    __redis_pool = {}
    __redis_client = {}
    __mutex = threading.Lock()

    @classmethod
    def __init_instance(cls, schema, redis_index):
        """
        初始化连接实例
        :param schema: 指定的schema
        :param redis_index: 指定的index
        :return: 无
        """
        schema = u'{0}{1}'.format(schema, redis_index)
        if schema not in cls.__redis_pool.keys():
            cls.__mutex.acquire()
            if schema not in cls.__redis_pool.keys():
                cls.__redis_pool[schema] = redis.ConnectionPool(
                    host=REDIS_CONFIG[ENVIRONMENT][schema][u'host'],
                    port=REDIS_CONFIG[ENVIRONMENT][schema][u'port'],
                    db=redis_index,
                    password=REDIS_CONFIG[ENVIRONMENT][schema][u'auth'],
                    encoding=REDIS_CONFIG[ENVIRONMENT][schema][u'encoding'],
                    max_connections=1
                )
                cls.__redis_client[schema] = redis.Redis(connection_pool=cls.__redis_pool[schema])
            cls.__mutex.release()

    @classmethod
    def __get_client(cls, schema, redis_index):
        """
        获取redis连接
        :param schema: 指定的schema
        :param redis_index: 指定的index
        :return: redis连接实例
        """
        cls.__init_instance(schema, redis_index)
        schema = u'{0}{1}'.format(schema, redis_index)
        return cls.__redis_client[schema]

    @classmethod
    def list_keys(cls, schema, keys_pattern, redis_index):
        """
        列出当前的redis连接key列表
        :param schema: 指定的schema
        :param keys_pattern: 正则
        :param redis_index: 指定的index
        :return: key列表
        """
        while 1:
            try:
                key_list = []
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                temp_key_list = r.keys(keys_pattern)
                for temp_key in temp_key_list:
                    key_list.append(temp_key)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)
        return key_list

    @classmethod
    def lpop(cls, schema, key, size, redis_index):
        """
        lpop
        :param schema: 指定的schema
        :param key: key名
        :param size: pop的个数
        :param redis_index: 指定的index
        :return: 获取的结果列表
        """
        while 1:
            pop_items = []
            try:
                i = 0
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                pipe = r.pipeline()
                while i < size:
                    pipe.lpop(key)
                    i += 1
                temp_pop_items = pipe.execute()
                for temp_item in temp_pop_items:
                    if temp_item is not None:
                        pop_items.append(temp_item)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)
        return pop_items

    @classmethod
    def rpush(cls, schema, key, json_text, redis_index):
        """
        rpush
        :param schema: 指定的schema
        :param key: key名
        :param json_text: json字符串
        :param redis_index: 指定的index
        :return: 无
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                r.rpush(key, json_text)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)

    @classmethod
    def lpush(cls, schema, key, json_text, redis_index):
        """
        lpush
        :param schema: 指定的schema
        :param key: key名
        :param json_text: json字符串
        :param redis_index: 指定的index
        :return: 无
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                r.lpush(key, json_text)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)

    @classmethod
    def rpush_list(cls, schema, key, json_text_array, redis_index):
        """
        批量rpush
        :param schema: 指定的schema
        :param key: key名
        :param json_text_array: json字符串列表
        :param redis_index: 指定的index
        :return: 无
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                pipe = r.pipeline()
                for json_text in json_text_array:
                    pipe.rpush(key, json_text)
                pipe.execute()
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)

    @classmethod
    def reconnect(cls, schema, redis_index):
        """
        重置连接
        :param schema: 指定的schema
        :param redis_index: 指定的index
        :return: 无
        """
        keys = copy.deepcopy(list(cls.__redis_pool.keys()))
        if schema in keys:
            try:
                cls.__redis_pool[schema].disconnect()
                cls.__redis_pool.pop(schema)
                cls.__redis_client.pop(schema)
            except Exception as e:
                logging.exception(e)
        cls.__init_instance(schema, redis_index)

    @classmethod
    def get_list_length(cls, schema, key, redis_index):
        """
        获取redis队列的长度
        :param schema: 指定的schema
        :param key: key名
        :param redis_index: 指定的index
        :return: 长度
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                length = r.llen(key)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)
        return length

    @classmethod
    def hash_set(cls, schema, hash_key, field, json_text, redis_index, expired_in=-1):
        """
        hash设置
        :param schema: 指定的schema
        :param hash_key: hash key
        :param field:
        :param json_text: json字符串
        :param redis_index: 指定的index
        :param expired_in: ttl
        :return: 无
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                pipe = r.pipeline()
                pipe.hset(hash_key, field, json_text)
                if expired_in != -1:
                    temp_expire = datetime.timedelta(days=0, seconds=expired_in)
                    pipe.expire(hash_key, temp_expire)
                pipe.execute()
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)

    @classmethod
    def hash_get(cls, schema, hash_key, field, redis_index):
        """
        获取redis的hash对象
        :param schema: 指定的schema
        :param hash_key: hash key
        :param field:
        :param redis_index: 指定的index
        :return: 获取到的结果
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                result = r.hget(hash_key, field)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)
        return result

    @classmethod
    def delete(cls, schema, key, redis_index=None):
        """
        删除指定的key
        :param schema: 指定的schema
        :param key: 指定的key
        :param redis_index: 指定的index
        :return: 无
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                r.delete(key)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)

    @classmethod
    def exists(cls, schema, key, redis_index=None):
        """
        判断key是否存在
        :param schema: 指定的schema
        :param key: key
        :param redis_index: 指定的index
        :return: 是否存在
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                status = r.exists(key)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)
        return status

    @classmethod
    def hash_increment_by(cls, schema, hash_key, field, redis_index, amount=1):
        """
        hash步进
        :param schema: 指定的schema
        :param hash_key: hash key
        :param field: 
        :param redis_index: 指定的index
        :param amount: 步长
        :return: 
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                r.hincrby(hash_key, field, amount)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)
                cls.reconnect(schema, redis_index)

    @classmethod
    def expire_valid_time(cls, schema, key, seconds, redis_index=None):
        """
        设置key的过期时间
        :param schema: 指定的schema
        :param key: key
        :param seconds: 秒
        :param redis_index: 指定的index
        :return: 无
        """
        while 1:
            try:
                r = cls.__get_client(schema, redis_index)
                cls.__mutex.acquire()
                r.expire(key, seconds)
                cls.__mutex.release()
                break
            except Exception as e:
                logging.exception(e)

    @classmethod
    def close(cls):
        """
        关闭所有的redis连接
        :return: 无
        """
        keys = copy.deepcopy(list(cls.__redis_pool.keys()))
        for schema in keys:
            try:
                cls.__redis_pool[schema].disconnect()
                cls.__redis_pool.pop(schema)
                cls.__redis_client.pop(schema)
            except Exception as e:
                logging.exception(e)
