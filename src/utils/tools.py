# -*- coding: utf-8 -*-
import codecs
import datetime
import hashlib
import hmac
import json
import logging
import os
import platform
import random
import re
import sys
import time
from logging.handlers import RotatingFileHandler

import gevent
import magic

if sys.version_info < (3, 4):
    import cPickle
    from urllib import quote
    from urllib import urlencode
else:
    import pickle as cPickle
    from urllib.parse import quote
    from urllib.parse import urlencode


def allot_logger(name=None, filename=None, level=None, formatter=None):
    """
    初始化一个logger
    :param name: logger名称
    :param filename: 日志文件路径
    :param level: 控制台日志输出级别，通常为debug、info、warning、error或critical
    :param formatter: 日志格式
    :return:
    """
    if filename is None:
        filename = u'logs/iCrawler.log'
    if level is None:
        level = logging.DEBUG
    else:
        level = eval('logging.{0}'.format(level.upper()))
    if formatter is None:
        formatter = (u'%(asctime)s %(levelname)s %(processName)s %(threadName)s %(module)s.%(funcName)s '
                     u'Line:%(lineno)d - %(message)s')
    fmt = logging.Formatter(formatter)
    logger = logging.getLogger(name)
    # log等级总开关，此处的日志级别需要尽可能的低。控制台和文件输出可以单独设置更高且相互不同的日志输出等级
    logger.setLevel(logging.NOTSET)
    # 控制台输出设置
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(level)
    # 日志文件输出设置（按照时间。也可以按照日志大小，使用RotatingFileHandler）
    # file_handler = TimedRotatingFileHandler(filename=filename, when=u'H', backupCount=1)
    # file_handler.setFormatter(fmt)
    # file_handler.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(filename=filename, maxBytes=50*1024*1024, backupCount=5)
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    # 可以仿照上面的handler设置方式，添加别的handler。eg，如果需要将日志发送到日志服务器时，使用SocketHandler或HTTPHandler
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)


def check_run_time(params):
    """
    检查运行时间
    :param params: 参数
    :return: 无
    """
    if params[u'run_schema'] == u'always':
        pass
    elif params[u'run_schema'] == u'repeat':
        while 1:
            try:
                is_valid = False
                for item_val in params[u'valid_time']:
                    time_list = item_val.split(u'-')
                    start_value = time_list[0]
                    end_value = time_list[1]
                    now_value = u'{0}/{1}'.format(
                        datetime.datetime.now().weekday() + 1,
                        str(datetime.datetime.now().time())[:5]
                    )

                    if start_value <= end_value:  # 本周内
                        if start_value <= now_value <= end_value:
                            is_valid = True
                    else:  # 跨周
                        if start_value <= now_value <= u'7/25:00' or u'0/00:00' <= now_value <= end_value:
                            is_valid = True

                    if is_valid:
                        break

                # 判断是否是有效运行时间，是就跳出循环，否则休眠10s
                if is_valid:
                    logging.debug(u'Valid running time.')
                    break
                else:
                    logging.debug(u'Not valid running time!')
                    gevent.sleep(10)
            except Exception as e:
                logging.exception(u'check run time error! - {0}'.format(e.message))
                gevent.sleep(1)
    else:
        raise Exception(u'Invalid run time schema!')


def days_before(n):
    """
    获取前n天（或后n天，此时n传负值）
    :param n: 天数
    :return: yyyy-MM-dd格式的字符串结果
    """
    # 获取当前的日期
    today = datetime.date.today()
    # 时间间隔
    timedelta = datetime.timedelta(days=n)
    return str(today - timedelta)


def md5(text, salt=None):
    """
    将文本值进行MD5
    :param text: 原始文本
    :param salt: 盐
    :return: MD5之后的结果
    """
    if not isinstance(text, bytes):
        text = text.encode(u'utf-8')
    if salt and not isinstance(salt, bytes):
        salt = salt.encode(u'utf-8')
    if salt:
        m = hashlib.md5(salt)
    else:
        m = hashlib.md5()
    m.update(text)
    return m.hexdigest()


def sha512(text, salt=None):
    """
    将文本进行sha512加密
    :param text: 原始文本
    :param salt: 盐
    :return: 加密结果
    """
    if not isinstance(text, bytes):
        text = text.encode(u'utf-8')
    if salt and not isinstance(salt, bytes):
        salt = salt.encode(u'utf-8')
    if salt:
        m = hashlib.sha512(salt)
    else:
        m = hashlib.sha512()
    m.update(text)
    return m.hexdigest()


def hmac_sha512(key, text):
    """
    将文本进行hmac_sha512加密
    :param key: 秘钥
    :param text: 原始文本
    :return: 加密结果
    """
    if not isinstance(key, bytes):
        key = key.encode(u'utf-8')
    if not isinstance(text, bytes):
        text = text.encode(u'utf-8')
    h = hmac.new(key, text, hashlib.sha512)
    return h.hexdigest()


def build_plugin_id(param):
    """
    根据配置参数构造插件的ID
    :param param: 配置参数
    :return: ID
    """
    text = u''
    if isinstance(param, dict):
        text += encrypt_dict(param)
    elif isinstance(param, (list, tuple, set)):
        text += encrypt_list(param)
    else:
        text += md5(str(param))
    return md5(text)


def encrypt_dict(dictionary):
    """
    加密字典型参数
    :param dictionary: 字典型参数
    :return: 加密结果
    """
    text = u''
    sorted_keys = sorted(dictionary.keys())
    for key in sorted_keys:
        try:
            if isinstance(dictionary[key], dict):
                text += encrypt_dict(dictionary[key])
            elif isinstance(dictionary[key], (set, tuple, list)):
                text += encrypt_list(list(dictionary[key]))
            else:
                text += md5(str(dictionary[key]))
        except Exception as e:
            logging.exception(e.message)
    return md5(text)


def encrypt_list(array):
    """
    加密数组类型参数
    :param array: 数组参数
    :return: 加密结果
    """
    text = u''
    for element in array:
        try:
            if isinstance(element, dict):
                text += encrypt_dict(element)
            elif isinstance(element, (list, tuple, set)):
                text += encrypt_list(element)
            else:
                text += md5(str(element))
        except Exception as e:
            logging.exception(e.message)
    return md5(text)


def pickle_read_file(filename):
    """
    使用pickle读文件
    :param filename: 文件名
    :return: 读取结果
    """
    result = None
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            try:
                result = cPickle.load(f)
            except Exception as e:
                remove_file(filename)
                logging.exception(e.message)
    return result


def pickle_write_file(filename, record):
    """
    使用pickle写文件
    :param filename: 文件名
    :param record: 需要写入文件的记录
    :return: 无
    """
    with open(filename, 'wb') as f:
        cPickle.dump(record, f, protocol=2)
        f.flush()


def write_file(filename, text, add=False):
    """
    写文件
    :param filename: 文件名
    :param text: 需要写入文件的内容
    :param add: 是否追加
    :return: 无
    """
    mode = u'a' if add else u'w'
    # 格式化文件内容
    if isinstance(text, (list, dict, tuple, set)):
        text = json.dumps(text, ensure_ascii=False)
    elif isinstance(text, (int, float, long)):
        text = str(text)
    elif isinstance(text, str):
        text = json.loads(json.dumps({u'text': text}))[u'text']
    with codecs.open(filename, mode, u'utf-8') as f:
        f.write(text)


def read_file(filename):
    """
    读文件
    :param filename: 文件名
    :return: 无
    """
    with codecs.open(filename, u'r', u'utf-8') as f:
        text = f.read()
    return text


def list_folder_files(path):
    """
    列出目录下的所有文件
    :param path: 目录
    :return: 文件名列表
    """
    file_names = []
    if os.path.exists(path):
        parents = os.listdir(path)
        for item in parents:
            if os.path.isfile(os.path.join(path, item)):
                file_names.append(os.path.join(path, item))
    return file_names


def remove_file(file_path):
    """
    移除文件
    :param file_path: 文件路径
    :return: 无
    """
    try:
        if os.path.exists(str(file_path)):
            os.remove(file_path)
    except Exception as e:
        logging.exception(u'remove file error! - {0}'.format(e.message))


def is_image(file_buffer):
    """
    判断是否是图片
    :param file_buffer: 文件流
    :return: 判断结果
    """
    status = False
    if file_buffer:
        system = platform.system()
        if system == u'Windows':
            m = magic.Magic(magic_file=u'C:\Windows\System32\magic.mgc')
        else:
            m = magic
        file_type = m.from_buffer(file_buffer)
        if u'image' in file_type.lower():
            status = True
    return status


def clean_mongodb_service_id(id_record):
    """
    清洗从mongodb服务获取的_id数据
    :param id_record: id数据
    :return: 清洗后的结果
    """
    return id_record[u'$oid']


def random_char_num(size, upper_mix=False):
    """
    随机数字与字母混合的、长度为size的字符串
    :param size: 结果长度
    :param upper_mix: 英文字母是否混合大小写
    :return: 随机结果
    """
    random_char = u''
    if upper_mix:
        numbers = u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    else:
        numbers = u'abcdefghijklmnopqrstuvwxyz0123456789'
    for i in range(size):
        random_char += numbers[random.randint(0, len(numbers) - 1)]
    return random_char


def random_num(size):
    """
    随机指定长度的数字
    :param size:
    :return:
    """
    first_nums = list(irange(1, 10))
    common_nums = list(irange(0, 10))
    result_list = []
    for i in irange(0, size):
        if i == 0:
            result_list.append(str(random.choice(first_nums)))
        else:
            result_list.append(str(random.choice(common_nums)))
    return u''.join(result_list)


def timestamp(size=10):
    """
    获取时间戳
    :param size: 长度
    :return: 指定长度的时间戳
    """
    if size == 10:
        millis = str(time.time()).split('.')[0]
    elif size == 13:
        millis = str(int(time.time() * 1000)).split('.')[0]
    else:
        if 0 < size < 13:
            millis = str(int(time.time() * 1000)).split('.')[0][:size]
        else:
            millis = str(int(time.time() * 1000)).split('.')[0] + '0' * (size - 13)
    return millis


def date_format_by_timestamp(stamp):
    """
    根据时间戳格式化日期数据
    :param stamp: 时间戳
    :return: 转化结果
    """
    if isinstance(stamp, (int, float, long)):
        temp_stamp = str(stamp)
        pieces = temp_stamp.split(u'.')
        if len(pieces) == 2 and len(pieces[0]) == 10:
            return time.strftime(u'%Y-%m-%d %H:%M:%S', time.localtime(stamp))
        elif len(pieces) == 1 and len(pieces[0]) == 10:
            return time.strftime(u'%Y-%m-%d %H:%M:%S', time.localtime(stamp))
        else:
            return date_format_by_timestamp(pieces[0])
    else:
        stamp = str(stamp)
        if u'.' in stamp:
            return date_format_by_timestamp(float(stamp))
        elif len(stamp) >= 10:
            stamp = stamp[:10] + u'.' + stamp[10:]
            return date_format_by_timestamp(float(stamp))
        else:
            return date_format_by_timestamp(stamp + u'0' * (10 - len(stamp)))


def irange(start, stop, step=1):
    """
    自定义range函数
    :param start: 其实数字（包括）
    :param stop: 结束数字（不包括）
    :param step: 步幅
    :return: 遍历器对象
    """
    if start is None or stop is None or not step:
        raise Exception(u'Params must be inited! - start({0}),stop({1}),step({2})'.format(start, stop, step))
    if sys.version_info < (3, 4):
        exe_str = 'xrange(start, stop, step)'
    else:
        exe_str = 'range(start, stop, step)'
    return eval(exe_str)


def get_params_from_url(url):
    """
    从url中获取相关参数
    :param url: url
    :return: 参数集合
    """
    params = dict()
    try:
        url_items = url.split(u'?')
        if len(url_items) == 2:
            url_params = url_items[1].split(u'&')
            for param in url_params:
                values = param.split(u'=')
                if len(values) == 2:
                    params[values[0]] = values[1]
    except Exception as e:
        logging.exception(u'get_params_from_url error! - {0}'.format(e.message))
    return params


def iquote(param, safe='/'):
    """
    对参数进行URL加密
    :param param: 参数
    :param safe: safe
    :return: 加密结果
    """
    return quote(param, safe)


def iurlencode(params):
    """
    对参数集进行URL加密
    :param params: 参数集合
    :return: 加密结果
    """
    return urlencode(params)


def random_ip():
    """
    随机IP
    :return:
    """
    prefix = random.choice([36, 61, 106, 121, 123, 139, 171, 182, 210, 222, 202])
    random_num0 = random.randint(2, 253)
    random_num1 = random.randint(2, 253)
    random_num2 = random.randint(2, 253)
    ip = u'{0}.{1}.{2}.{3}'.format(prefix, random_num0, random_num1, random_num2)
    return ip


def clean_tags(content, split, tag_names, target):
    """
    清洗标签数据
    :param content: 原文内容
    :param split: 分隔符
    :param tag_names: 标签名
    :param target: 目标标签
    :return: 目标结果
    """
    result = u''
    try:
        items = content.split(split)
        for index00 in irange(0, len(items) - 1):
            if target in items[index00]:
                result = items[index00 + 1]
                for tag in tag_names:
                    result = result.replace(tag, u'')
                break
    except Exception as e:
        logging.exception(e.message)
    return result.strip()


def trim_blanks(text):
    """
    清空文本中的空格
    :param text: 需要进行操作的原始文本
    :return: 操作之后的文本
    """
    noise_list = [u' ', u' ', u'　', u' ', u'\r', u'\n', u'\t']
    return trim_noises(text, noise_list)


def trim_brackets(text):
    """
    清空文本中各类括号
    :param text: 需要进行操作的原始文本
    :return: 操作之后的文本
    """
    noise_list = [
        u'(', u')', u'<', u'>', u'[', u']', u'{', u'}', u'《', u'》', u'【', u'】', u'（', u'）', u'［', u'］', u'〔',
        u'〕', u'／', u'/'
    ]
    return trim_noises(text, noise_list)


def trim_alphas(text):
    """
    清空文本中所有的英文字母
    :param text: 需要进行操作的原始文本
    :return: 操作之后的文本
    """
    return trim_noises(text.lower(), [chr(i) for i in range(97, 123)])


def trim_numbers(text):
    """
    清空文本中所有的数字
    :param text: 需要进行操作的原始文本
    :return: 操作之后的文本
    """
    return trim_noises(text, [u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9'])


def trim_noises(text, noise_list):
    """
    清空文本中指定内容的噪音
    :param text: 需要进行操作的原始文本
    :param noise_list: 噪音列表
    :return: 操作之后的文本
    """
    for noise in noise_list:
        text = text.replace(noise, u'')
    return text.strip()


def trim_list(rec_list):
    """
    清空list中的空值（子字典和子列表会递归清空）
    :param rec_list: 原始数据列表
    :return: 清除空值之后的数据列表
    """
    result_list = list()
    for rec in rec_list:
        if not rec:
            continue
        if isinstance(rec, dict):
            temp_rec = trim_dict(rec)
            if temp_rec:
                result_list.append(temp_rec)
        elif isinstance(rec, list):
            temp_rec = trim_list(rec)
            if temp_rec:
                result_list.append(temp_rec)
        elif isinstance(rec, (tuple, set, int, float, long)):
            result_list.append(rec)
        elif isinstance(rec, (unicode, str, bytes)):
            temp_rec = trim_blanks(rec)
            if temp_rec:
                result_list.append(temp_rec)
    return result_list


def trim_dict(rec_dict):
    """
    清空字典中的空值（子字典和子列表会递归清空）
    :param rec_dict: 原始数据字典
    :return: 清除空值之后的数据字典
    """
    result_dict = dict()
    for key in rec_dict.keys():
        rec = rec_dict[key]
        if not rec:
            continue
        if isinstance(rec, dict):
            temp_rec = trim_dict(rec)
            if temp_rec:
                result_dict[key] = temp_rec
        elif isinstance(rec, list):
            temp_rec = trim_list(rec)
            if temp_rec:
                result_dict[key] = temp_rec
        elif isinstance(rec, (tuple, set, int, float, long)):
            result_dict[key] = rec
        elif isinstance(rec, (unicode, str, bytes)):
            temp_rec = trim_blanks(rec)
            if temp_rec:
                result_dict[key] = temp_rec
    return result_dict


def regular(expression, text):
    """
    找出文字中符合正则表达式的所有字符列表
    :param expression: 正则表达式
    :param text: 文本内容
    :return: 筛选结果
    """
    return re.findall(expression, text)


def regular_numbers(text):
    """
    使用正则表达式提取文本中所有的数字，以列表的形式返回
    :param text: 原始文本
    :return: 数字列表
    """
    return regular(r'\d+', text)


def regular_by_scope(start, end, text, schema=0):
    """
    使用正则表达式提取文本中指定首尾范围的所有字符，以列表的形式返回
    :param start: 起始字符
    :param end: 结尾字符
    :param text: 原始文本
    :param schema: 匹配模式
        0-不包含起始字符和结尾字符
        1-包含起始字符，不包含结尾字符
        2-不包含起始字符，包含结尾字符
        3-包含起始字符和结尾字符
    :return: 结果列表
    """
    if schema == 0:
        expression = r'(?<=%s)(.+?)(?=%s)' % (start, end)
    elif schema == 1:
        expression = r'(?=%s)(.+?)(?=%s)' % (start, end)
    elif schema == 2:
        expression = r'(?<=%s)(.+?)(?<=%s)' % (start, end)
    elif schema == 3:
        expression = r'(?=%s)(.+?)(?<=%s)' % (start, end)
    else:
        raise ValueError(u'Invalid schema value! Param schema must be in [0, 1, 2, 3]! - schema:{0}'.format(schema))
    return regular(expression, text)


def check_query_key_valid(query_key):
    """
    检查查询参数的有效性
    :param query_key: 查询参数
    :return: 检查结果
    """
    valid = True
    if not query_key:
        valid = False
    else:
        query_key = trim_noises(trim_alphas(trim_blanks(trim_brackets(trim_numbers(query_key)))), [u'*', u'无'])
        if len(query_key) < 2 or len(query_key) > 30:
            valid = False
    return valid
