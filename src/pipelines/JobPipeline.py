# -*- coding: utf-8 -*-
import datetime
import uuid

from src.config import PROCESS_TOPIC_CONFIG, ENVIRONMENT, OTS_INSTANCE_CONFIG
from src.cores.pipeline import Pipeline
from src.utils import tools


class JobPipeline(Pipeline):
    """招聘数据结果处理"""

    def __init__(self):
        super(JobPipeline, self).__init__()
        self.data_type = u'qy_job'
        self.kafka = PROCESS_TOPIC_CONFIG[ENVIRONMENT]
        self.ots_instance = OTS_INSTANCE_CONFIG[u'DATA'][ENVIRONMENT]
        table_config = {
            u'LOCALHOST': u'test_parsed_data',
            u'SIT': u'test_parsed_data',
            u'PROD': u'prod_parsed_data'
        }
        self.ots_table = table_config[ENVIRONMENT]

    def process_item(self, config, result, message):
        """
        处理结果，将数据发往下一步进行处理
        :param config: 配置
        :param result: 处理后的消息对象
        :param message: 查询参数
        :return: 无
        """
        self.transfer_none_to_empty_str(result)
        data_id = str(uuid.uuid4())
        # 构造流向卡夫卡的数据
        kafka_record = message
        kafka_record[u'_type'] = self.data_type
        kafka_record[u'_dataid'] = data_id
        if u'_traceid' not in kafka_record.keys() or not kafka_record.get(u'_traceid'):
            kafka_record[u'_traceid'] = tools.random_char_num(18, True)
        if u'_sent_time' not in kafka_record.keys() or not kafka_record.get(u'_sent_time'):
            kafka_record[u'_sent_time'] = datetime.datetime.now().strftime(u'%Y-%m-%d %H:%M:%S')
        # 构造流向OTS的数据
        result[u'eid'] = self.build_ent_eid_by_name(result[u'name'])
        pk = [{u'_dataid': data_id}]
        columns = {u"parsed_data": result}

        self.flow_to_ots(self.ots_instance, self.ots_table, pk, columns)
        self.flow_to_kafka(self.kafka, kafka_record)
