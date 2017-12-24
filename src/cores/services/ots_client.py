# -*- coding: utf-8 -*-
import copy
import json
import logging

from src.config import OTS_CONFIG, ENVIRONMENT
from src.cores.customer import CustomerJsonEncoder
from src.cores.services import http_client


def ots_service_put_row(instance_name, table_name, pk, data_json):
    """
    上传OTS数据
    :param instance_name:
    :param table_name:
    :param pk: [{"dataid":"1111"}, {"dataid": "2222"}]
    :param data_json: {"col1": "1111", "col2": "222"}
    :return:
    """
    url = u'http://{0}:{1}/ots/put_row?_=0'.format(OTS_CONFIG[ENVIRONMENT][u'host'], OTS_CONFIG[ENVIRONMENT][u'port'])
    # 检查data_json
    new_data_json = copy.copy(data_json)
    for i in pk:
        pk_key = i.keys()[0]
        if pk_key in new_data_json.keys():
            new_data_json.pop(pk_key, None)
            logging.warning(
                u"data json including PK column - " + pk_key + u", will remove it from data json automatically.")
    req_data = {
        u"instance_name": instance_name,
        u"tablename": table_name,
        u"pk": json.dumps(pk, ensure_ascii=False, cls=CustomerJsonEncoder),
        u"columns": json.dumps(new_data_json, ensure_ascii=False, cls=CustomerJsonEncoder)
    }
    return (http_client.do_http_post(url, data=req_data))[0]


def ots_service_get_row(instance_name, table_name, pk, columns):
    """
    获取OTS 数据
    :param instance_name:
    :param table_name:
    :param pk: [{"dataid":"1111"}, {"dataid": "2222"}]
    :param columns: ["col1", "col2"]
    :return:
    """
    url = u'http://{0}:{1}/ots/get_row?_=0'.format(OTS_CONFIG[ENVIRONMENT][u'host'], OTS_CONFIG[ENVIRONMENT][u'port'])
    req_data = {
        u"instance_name": instance_name,
        u"tablename": table_name,
        u"pk": json.dumps(pk, ensure_ascii=False, cls=CustomerJsonEncoder),
        u"columns": json.dumps(columns, ensure_ascii=False, cls=CustomerJsonEncoder)
    }
    return json.loads((http_client.do_http_post(url, data=req_data))[0])


def ots_service_update_row(instance_name, table_name, pk, columns, columns_delete):
    """
    更新OTS数据
    :param instance_name:
    :param table_name:
    :param pk: [{"pk_col1":"1111"}, {"pk_col2": "2222"}]
    :param columns:
    :param columns_delete:
    :return:
    """
    url = u'http://{0}:{1}/ots/update_row?_=0'.format(
        OTS_CONFIG[ENVIRONMENT][u'host'], OTS_CONFIG[ENVIRONMENT][u'port'])
    req_data = {
        u"instance_name": instance_name,
        u"tablename": table_name,
        u"pk": json.dumps(pk, ensure_ascii=False, cls=CustomerJsonEncoder),
        u"columns": json.dumps(columns, ensure_ascii=False, cls=CustomerJsonEncoder),
        u"columns_delete": json.dumps(columns_delete, ensure_ascii=False, cls=CustomerJsonEncoder)
    }
    return (http_client.do_http_post(url, req_data))[0]
