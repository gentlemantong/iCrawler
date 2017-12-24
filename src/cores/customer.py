# -*- coding: utf-8 -*-
import json
import datetime
from bson import ObjectId


class CustomerJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime(u'%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime(u'%Y-%m-%d')
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)
