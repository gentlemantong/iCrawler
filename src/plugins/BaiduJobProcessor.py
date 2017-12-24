# -*- coding: utf-8 -*-
import json
import logging
import math

import gevent

from src.cores.process import Processor
from src.cores.services import http_client
from src.cores.services.mongodb_client import MongodbService
from src.items.JobItem import JobItem
from src.utils import tools


class BaiduJobProcessor(Processor):
    """百度招聘数据抓取脚本"""

    def __init__(self, config, source_queue, result_queue):
        super(BaiduJobProcessor, self).__init__(config, source_queue, result_queue)
        self.url = u'http://zhaopin.baidu.com/api/async'

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

        company = self.__get_query_key(message)
        if company in [u'name'] or not tools.check_query_key_valid(company):
            logging.error(u'Invalid message! - {0}'.format(json.dumps(message, ensure_ascii=False)))
            return max_page_no, list_records, None, has_detail

        base_keys = [
            u'salary', u'welfare', u'education', u'city', u'district', u'experience', u'employertype', u'jobfirstclass',
            u'jobsecondclass', u'jobthirdclass', u'date']
        params = dict.fromkeys(base_keys, u'')
        params[u'query'] = company
        params[u'sort_key'] = 5
        params[u'sort_type'] = 1
        params[u'detailmode'] = u'close'
        params[u'rn'] = 30
        params[u'pn'] = 30 * (page_no - 1)
        err_count = 0
        while err_count < self.retry_limit:
            try:
                self.refresh_proxy()
                resp_text = (http_client.do_http_get(
                    url=self.url,
                    params=params,
                    cookies=self.base_cookies,
                    proxies=self.base_proxies,
                    timeout=60
                ))[0]
                if resp_text:
                    max_page_no = self.__parse_list_page(list_records, resp_text)
                    break
            except Exception as e:
                logging.exception(e.message)
            err_count += 1
            gevent.sleep(1)
        return max_page_no, list_records, JobItem, has_detail

    def __parse_list_page(self, list_records, resp_text):
        """
        解析列表页数据
        :param list_records: 列表页数据集合
        :param resp_text: 页面数据
        :return: 最大页码
        """
        max_page_no = 1
        resp_json = json.loads(resp_text)
        if resp_json.get(u'data') and resp_json[u'data'].get(u'data'):
            base_data = resp_json[u'data'][u'data']
            # 最大页码
            if base_data.get(u'listNum'):
                max_page_no = math.ceil(float(base_data[u'listNum']) / 30.0)
            # 列表页数据
            if base_data.get(u'disp_data'):
                dis_data = base_data[u'disp_data']
                for data_n in dis_data:
                    try:
                        item = JobItem()
                        item.title = data_n[u'title']
                        item.salary = data_n[u'salary']
                        item.province = data_n.get(u'province', u'')
                        item.city = data_n.get(u'city', u'')
                        item.district = data_n.get(u'district', u'')
                        item.location = data_n.get(u'location', u'')
                        item.position = data_n.get(u'companyaddress', u'')
                        item.age = data_n.get(u'age', u'')
                        item.sex = data_n.get(u'sex', u'')
                        item.education = data_n.get(u'education', u'')
                        item.number = data_n.get(u'number', u'')
                        item.years = data_n.get(u'experience', u'')
                        item.job_class = self.__format_job_class(data_n)
                        item.job_type = data_n.get(u'type', u'')
                        item.description = data_n.get(u'description', u'')
                        item.department = data_n.get(u'depart', u'')

                        item.date = data_n[u'startdate']
                        item.end_date = data_n[u'enddate']
                        item.welfare_list = self.__format_welfare(data_n)

                        item.name = data_n[u'officialname']
                        item.ent_type = data_n.get(u'employertype', u'')
                        item.size = data_n.get(u'size', u'')
                        item.ent_ind = data_n.get(u'industry', u'')
                        item.ent_desc = data_n.get(u'companydescription', u'')
                        item.ent_url = tools.trim_blanks(data_n.get(u'employerurl', u''))
                        item.ent_logo = tools.trim_blanks(data_n.get(u'logo', u''))
                        item.ent_short_name = data_n.get(u'commonname', u'')
                        item.email = data_n[u'email'].replace(u'None', u'') if data_n.get(u'email') else u''

                        item.source = data_n[u'source']
                        item.url = data_n[u'url']
                        list_records.append(item)
                    except Exception as e:
                        logging.exception(e.message)
        return max_page_no

    @staticmethod
    def __format_welfare(data_n):
        """
        格式化公司福利数据
        :param data_n: 原始招聘数据
        :return: 格式化的公司福利数据
        """
        welfare = list()
        temp_welfare = data_n.get(u'welfare', u'')
        if isinstance(temp_welfare, list):
            welfare += temp_welfare
        elif isinstance(temp_welfare, (unicode, str)):
            noise_list = [u';', u'，', u' ', u' ', u'　', u' ', u'\r', u'\n', u'\t']
            for noise in noise_list:
                temp_welfare = temp_welfare.replace(noise, u',')
            welfare += list(tools.trim_list(temp_welfare.split(u',')))
        return welfare

    @staticmethod
    def __format_job_class(data_n):
        """
        格式化工作类型
        :param data_n: 原始招聘数据
        :return: 格式化后的工作类型
        """
        job_type = u''
        if data_n.get(u'jobfirstclass'):
            job_type = data_n[u'jobfirstclass']
        elif data_n.get(u'jobsecondclass'):
            job_type = data_n[u'jobsecondclass']
        return job_type

    @staticmethod
    def __get_query_key(message):
        """
        获取查询关键字
        :param message: 查询参数
        :return: 无
        """
        query_key = None
        temp_query_key = None
        if u'company' in message.keys():
            temp_query_key = message[u'company']
        elif u'key0' in message.keys():
            temp_query_key = message[u'key0'].replace(u'"', u'')

        # 判断企业是否是个体，个体不进行查询
        if temp_query_key:
            try:
                query_dict = {u'name': temp_query_key.replace(u'(', u'（').replace(u')', u'）')}
                resp_text = MongodbService.find_one(u'gs', u'e_cn_gs_basics', query_dict, [u'category'])
                if resp_text:
                    category = json.loads(resp_text)[u'category']
                    if category == u'E':
                        query_key = temp_query_key
                else:
                    query_key = temp_query_key
            except Exception as e:
                logging.exception(e.message)
        return query_key
