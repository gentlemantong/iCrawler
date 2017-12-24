# -*- coding: utf-8 -*-
import gevent
from gevent.queue import PriorityQueue

from src.cores import process
from src.cores import provider
from src.cores.pipeline import result_handler


def run(args):
    """
    开启子处理函数
    :param args:
    :return:
    """
    source_queue = PriorityQueue()
    result_queue = PriorityQueue()
    tasks = [
        gevent.spawn(provider.run, (args, source_queue)),
        gevent.spawn(process.run, (args, source_queue, result_queue))
    ]
    for i in range(args.task):
        tasks.append(gevent.spawn(result_handler, result_queue))
    gevent.joinall(tasks)
