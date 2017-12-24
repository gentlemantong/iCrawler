# -*- coding: utf-8 -*-
import json
import logging

from src.config import KAFKA_CONFIG, ENVIRONMENT, FLASK_SERVICE_CONFIG
from src.cores.customer import CustomerJsonEncoder
from src.cores.services import http_client


def poll(topic, group_id):
    """
    从kafka队列中获取一条消息
    :param topic: kafka的topic
    :param group_id: 对应topic的指定group_id
    :return: 消息数据
    """
    url = u'http://{0}:{1}/kafka/poll'.format(KAFKA_CONFIG[ENVIRONMENT][u'host'], KAFKA_CONFIG[ENVIRONMENT][u'port'])
    params = {
        u'topic_name': topic,
        u'group_id': group_id
    }
    return (http_client.do_http_get(url, params=params))[0]


def offer(topic, data):
    """
    向kafka队列发送一条消息
    :param topic: kafka的topic
    :param data: 需要发送的消息
    :return:
    """
    url = u'http://{0}:{1}/kafka/offer'.format(KAFKA_CONFIG[ENVIRONMENT][u'host'], KAFKA_CONFIG[ENVIRONMENT][u'port'])
    if isinstance(data, (dict, list, tuple, set)):
        data_str = json.dumps(data, ensure_ascii=False, cls=CustomerJsonEncoder)
    else:
        data_str = str(data)
    data = {
        u'topic_names': topic,
        u'data_str': data_str
    }
    return (http_client.do_http_post(url, data=data))[0]


def llen(topic, group=None):
    """
    获取kafka队列的长度
    :param topic: topic
    :param group: group（可选）
    :return: 长度
    """
    length = 0
    url = u'http://{0}:{1}/api/kafka/llen'.format(
        FLASK_SERVICE_CONFIG[ENVIRONMENT][u'host'], FLASK_SERVICE_CONFIG[ENVIRONMENT][u'port'])
    params = {u'topic': topic}
    if group:
        params[u'group'] = group
    try:
        length = eval((http_client.do_http_get(url, params=params))[0])[u'length']
    except Exception as e:
        logging.exception(e.message)
    return length
