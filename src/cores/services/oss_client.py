# -*- coding: utf-8 -*-
import json
import logging
import threading

import oss2

from src.config import OSS_CONFIG, ENVIRONMENT
from src.cores.customer import CustomerJsonEncoder
from src.cores.services import http_client


class OSSClient(object):
    """OSS相关方法"""
    
    __auth = None
    __service = None
    __mutex = threading.Lock()

    @classmethod
    def __init_conn(cls):
        """
        初始化连接
        :return: 无
        """
        if cls.__auth is None:
            # 初始化登录信息
            cls.__mutex.acquire()
            if cls.__auth is None:
                cls.__auth = oss2.Auth(
                    OSS_CONFIG[ENVIRONMENT][u'access_key_id'],
                    OSS_CONFIG[ENVIRONMENT][u'access_key_secret'])
            cls.__mutex.release()

    @classmethod
    def __get_service(cls):
        """
        获取连接
        :return: 无
        """
        cls.__init_conn()
        if cls.__service is None:
            cls.__mutex.acquire()
            if cls.__service is None:
                if OSS_CONFIG[ENVIRONMENT][u'timeout'] is None:
                    cls.__service = oss2.Service(cls.__auth, OSS_CONFIG[ENVIRONMENT][u'end_point'])
                else:
                    # 设置连接超时
                    cls.__service = oss2.Service(
                        cls.__auth, OSS_CONFIG[ENVIRONMENT][u'end_point'],
                        connect_timeout=OSS_CONFIG[ENVIRONMENT][u'timeout']
                    )
            cls.__mutex.release()

    @classmethod
    def __get_bucket(cls, bucket_name):
        """
        获取bucket对象
        :param bucket_name: bucket名
        :return: bucket对象
        """
        cls.__init_conn()
        bucket = oss2.Bucket(cls.__auth, OSS_CONFIG[ENVIRONMENT][u'end_point'], bucket_name)
        return bucket

    @classmethod
    def list_buckets(cls):
        """
        列出该service下的所有bucket
        :return: bucket名列表
        """
        cls.__get_service()
        cls.__mutex.acquire()
        list_buckets = oss2.BucketIterator(cls.__service)
        cls.__mutex.release()
        return list_buckets

    @classmethod
    def new_bucket(cls, bucket_name, root=None):
        """
        新建一个bucket
        :param bucket_name: bucket名
        :param root: 权限
        :return: 无
        """
        bucket = cls.__get_bucket(bucket_name)
        cls.__mutex.acquire()
        if root is None:
            bucket.create_bucket()
        else:
            # 设置bucket权限
            root = eval('oss2.%s' % root)
            bucket.create_bucket(root)
        cls.__mutex.release()

    @classmethod
    def delete_bucket(cls, bucket_name):
        """
        删除指定的bucket
        :param bucket_name: bucket名
        :return: 无
        """
        bucket = cls.__get_bucket(bucket_name)
        try:
            cls.__mutex.acquire()
            bucket.delete_bucket()
            cls.__mutex.release()
        except oss2.exceptions.BucketNotEmpty:
            logging.exception('bucket is not empty.')
        except oss2.exceptions.NoSuchBucket:
            logging.exception('bucket does not exist')

    @classmethod
    def view_bucket_root(cls, bucket_name):
        """
        查看bucket的权限
        :param bucket_name: bucket名
        :return: 权限
        """
        bucket = cls.__get_bucket(bucket_name)
        cls.__mutex.acquire()
        acl = bucket.get_bucket_acl().acl
        cls.__mutex.release()
        return acl

    @classmethod
    def set_bucket_root(cls, bucket_name, root):
        """
        设置bucket权限
        :param bucket_name: bucket名
        :param root: 权限
        :return: 无
        """
        bucket = cls.__get_bucket(bucket_name)
        cls.__mutex.acquire()
        root = eval('oss2.%s' % root)
        bucket.put_bucket_acl(root)
        cls.__mutex.release()

    @classmethod
    def upload_file_buffer(cls, bucket_name, filename, file_obj):
        """
        可以上传字符串、Bytes、Unicode、二进制文件流、iterable等文本内容
        :param bucket_name: bucket名
        :param filename: 文件名
        :param file_obj: 文件对象
        :return: 执行结果
        """
        bucket = cls.__get_bucket(bucket_name)
        cls.__mutex.acquire()
        result = bucket.put_object(filename, file_obj)
        cls.__mutex.release()
        return result

    @classmethod
    def upload_file(cls, bucket_name, filename, local):
        """
        上传本地文件
        :param bucket_name: bucket名
        :param filename: 文件名
        :param local: 本地路径
        :return: 执行结果
        """
        bucket = cls.__get_bucket(bucket_name)
        cls.__mutex.acquire()
        result = bucket.put_object_from_file(filename, local)
        cls.__mutex.release()
        return result

    @classmethod
    def upload_resume(cls, bucket_name, filename, local):
        """
        设置断点续传参数
        :param bucket_name: bucket名
        :param filename: 文件名
        :param local: 本地路径
        :return: 无
        """
        bucket = cls.__get_bucket(bucket_name)
        cls.__mutex.acquire()
        oss2.resumable_upload(
            bucket, filename, local, store=oss2.ResumableStore(root='cache'), multipart_threshold=100 * 1024,
            part_size=100 * 1024, num_threads=4
        )
        cls.__mutex.release()


class OSSService(object):
    """二次封装的OSS服务"""

    @staticmethod
    def put_text(bucket_name, folder_name, filename, text):
        """
        将文本存到指定的位置
        :param bucket_name: bucket的名称
        :param folder_name: 文件夹名
        :param filename: 文件名
        :param text: 文本内容
        :return: 操作结果
        """
        url = u'http://{0}:{1}/oss/put_text'.format(
            OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'host'], OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'port'])
        if isinstance(text, (dict, list, tuple, set)):
            text = json.dumps(text, cls=CustomerJsonEncoder)
        data = {
            u'bucket_name': bucket_name,
            u'foldername': folder_name,
            u'filename': filename,
            u'text': text,
        }
        return (http_client.do_http_post(url, data=data, timeout=100))[0]

    @staticmethod
    def get_text(bucket_name, folder_name, filename):
        """
        获取指定的文件
        :param bucket_name: bucket的名称
        :param folder_name: 文件夹名
        :param filename: 文件名
        :return: 操作结果
        """
        url = u'http://{0}:{1}/oss/get_text'.format(
            OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'host'], OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'port'])
        params = {
            u'bucket_name': bucket_name,
            u'foldername': folder_name,
            u'filename': filename
        }
        return (http_client.do_http_get(url, params=params))[0]

    @staticmethod
    def copy_file(bucket_name, folder_from, folder_to, filename):
        """
        将文件从folder_from复制到folder_to
        :param bucket_name: bucket的名称
        :param folder_from: folder_from
        :param folder_to: folder_to
        :param filename: 文件名
        :return: 操作结果
        """
        url = u'http://{0}:{1}/oss/copy_file'.format(
            OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'host'], OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'port'])
        data = {
            u'bucket_name': bucket_name,
            u'from_foldername': folder_from,
            u'to_foldername': folder_to,
            u'filename': filename
        }
        return (http_client.do_http_post(url, data=data))[0]

    @staticmethod
    def exists(bucket_name, folder_name, filename):
        """
        判断一个文件是否存在
        :param bucket_name: bucket的名称
        :param folder_name: 文件夹名
        :param filename: 文件名
        :return: 查询结果
        """
        url = u'http://{0}:{1}/oss/exists'.format(
            OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'host'], OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'port'])
        params = {
            u'bucket_name': bucket_name,
            u'foldername': folder_name,
            u'filename': filename
        }
        return (http_client.do_http_get(url, params=params))[0]

    @staticmethod
    def put_file(bucket_name, folder_name, filename, base64_buffer):
        """
        将文件存到指定位置
        :param bucket_name: bucket的名称
        :param folder_name: 文件夹名
        :param filename: 文件名
        :param base64_buffer: 文件流
        :return: 操作结果
        """
        url = u'http://{0}:{1}/oss/put_base64_as_file'.format(
            OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'host'], OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'port'])
        data = {
            u'bucket_name': bucket_name,
            u'foldername': folder_name,
            u'filename': filename,
            u'base64': base64_buffer
        }
        return (http_client.do_http_post(url, data=data))[0]

    @staticmethod
    def list_files(bucket_name, folder_name, size=10, start_mark=False):
        """
        遍历指定文件夹下的文件
        :param bucket_name: bucket的名称
        :param folder_name: 文件夹名
        :param size: 获取的文件数量
        :param start_mark: 索引
        :return: 操作结果
        """
        url = u'http://{0}:{1}/oss/list'.format(
            OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'host'], OSS_CONFIG[u'SERVICE'][ENVIRONMENT][u'port'])
        data = {
            u'bucket_name': bucket_name,
            u'foldername': folder_name,
            u'size': size,
            u'startmarker': start_mark
        }
        return (http_client.do_http_post(url, data=data))[0]
