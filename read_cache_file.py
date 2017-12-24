# -*- coding: utf-8 -*-
import argparse
import json

from src.utils import tools


def get_args():
    """
    获取参数
    :return: 参数集合
    """
    args = argparse.ArgumentParser(description=u'get arguments for program.')
    args.add_argument(u'--filename', default=u'mongodb_gs_hot_companies.id', help=u'需要读取的文件名')
    return args.parse_args()


if __name__ == u'__main__':
    params = get_args()
    if not params.filename:
        print(u'Invalid filename!')
    else:
        value = tools.pickle_read_file(u'cache/{0}'.format(params.filename))
        if isinstance(value, (dict, list, tuple, set)):
            print json.dumps(value, ensure_ascii=False)
        else:
            print value
