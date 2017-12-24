# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import argparse
from src.utils import tools
from src.cores import launcher


def get_args():
    """
    获取参数
    :return: 参数集合
    """
    args = argparse.ArgumentParser(description=u'get arguments for program.')
    args.add_argument(u'--schema', default=u'STATIC', help=u'schema')
    args.add_argument(u'--log_level', default=u'debug', help=u'日志等级')
    args.add_argument(u'--task', type=int, default=1, help=u'并发量')
    return args.parse_args()


def run(args):
    """
    开始函数
    :param args: 运行参数
    :return: 无
    """
    log_file = u'logs/iCrawler_{0}.log'.format(args.schema)
    tools.allot_logger(filename=log_file, level=args.log_level)
    launcher.run(args)


if __name__ == u'__main__':
    params = get_args()
    run(params)
