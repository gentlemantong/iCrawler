# -*- coding: utf-8 -*-
ENVIRONMENT = u'DEV'
RESULT_QUEUE_MAX_SIZE = 1000
SOURCE_QUEUE_MAX_SIZE = 1000
CACHE_FILE_KEY = u'__cache_file__'

# 卡夫卡消息队列服务配置
KAFKA_CONFIG = {
    u'DEV': {
        u'host': u'',
        u'port': 0
    },
    u'SIT': {
        u'host': u'',
        u'port': 0
    },
    u'PROD': {
        u'host': u'',
        u'port': 0
    }
}

# flask服务配置
FLASK_SERVICE_CONFIG = {
    u'DEV': {
        u'host': u'',
        u'port': 0
    },
    u'SIT': {
        u'host': u'',
        u'port': 0
    },
    u'PROD': {
        u'host': u'',
        u'port': 0
    }
}

# mongodb配置
MONGODB_CONFIG = {
    u'SERVICE': {
        u'DEV': {
            u'host': u'',
            u'port': 0
        },         # 本地环境服务
        u'SIT': {
            u'host': u'',
            u'port': 0
        },               # 测试环境服务
        u'PROD': {
            u'host': u'',
            u'port': 0
        }               # 正式环境服务
    },               # 服务配置
    u'DEV_DEV': {
        u'host': u'',
        u'port': 0,
        u'db': u'',
        u'name': u'',
        u'password': u''
    },         # 开发库_本地连接
    u'PROD-iDATA_DEV': {
        u'host': u'',
        u'port': 0,
        u'db': u'',
        u'name': u'',
        u'password': u''
    },  # 正式iData库_本地连接
    u'PROD-iGS_DEV': {
        u'host': u'',
        u'port': 0,
        u'db': u'',
        u'name': u'',
        u'password': u''
    },    # 正式iGS库_本地连接
}

# mysql配置
MYSQL_CONFIG = {
    u'SERVICE': {
        u'DEV': {
            u'host': u'',
            u'port': 0
        },         # 本地环境服务
        u'SIT': {
            u'host': u'',
            u'port': 0
        },               # 测试环境服务
        u'PROD': {
            u'host': u'',
            u'port': 0
        }               # 正式环境服务
    },
    u'DEV': {
        u'host': u'',
        u'port': 0,
        u'db': u'',
        u'user': u'',
        u'password': u'',
        u'charset': u''
    },             # 本地MySQL连接
    u'DEV_DEV': {
        u'host': u'',
        u'port': 0,
        u'db': u'',
        u'user': u'',
        u'password': u'',
        u'charset': u''
    },         # 开发库_本地连接
}

# oss配置
OSS_CONFIG = {
    u'SERVICE': {
        u'DEV': {
            u'host': u'',
            u'port': 0
        },
        u'SIT': {
            u'host': u'',
            u'port': 0
        },
        u'PROD': {
            u'host': u'',
            u'port': 0
        }
    },
    u'DEV': {
        u'access_key_id': u'',
        u'access_key_secret': u'',
        u'end_point': u'',
        u'timeout': None
    },
    u'SIT': {
        u'access_key_id': u'',
        u'access_key_secret': u'',
        u'end_point': u'',
        u'timeout': None
    },
    u'PROD': {
        u'access_key_id': u'',
        u'access_key_secret': u'',
        u'end_point': u'',
        u'timeout': None
    },

}

# ots配置
OTS_CONFIG = {
    u'DEV': {
        u'host': u'',
        u'port': 0
    },
    u'SIT': {
        u'host': u'',
        u'port': 0
    },
    u'PROD': {
        u'host': u'',
        u'port': 0
    }
}

# redis配置
REDIS_CONFIG = {
    u'DEV': {
        u'R2M': {
            u'host': u'',
            u'port': 0,
            u'auth': u'',
            u'encoding': u'',
            u'index': 0,
        }
    },
    u'SIT': {
        u'R2M': {
            u'host': u'',
            u'port': 0,
            u'auth': u'',
            u'encoding': u'',
            u'index': 0,
        }
    },
    u'PROD': {
        u'R2M': {
            u'host': u'',
            u'port': 0,
            u'auth': u'',
            u'encoding': u'',
            u'index': 0,
        }
    }
}

# 代理配置
PROXY_CONFIG = {
    u'DEV': {
        u'host': u'',
        u'port': 0
    },
    u'SIT': {
        u'host': u'',
        u'port': 0
    },
    u'PROD': {
        u'host': u'',
        u'port': 0
    }
}

# 打码服务配置
DAMA_CONFIG = {
    u'DEV': {
        u'host': u'',
        u'port': 0
    },
    u'SIT': {
        u'host': u'',
        u'port': 0
    },
    u'PROD': {
        u'host': u'',
        u'port': 0
    }
}
DAMA_NACAO_CONFIG = {
    u'DEV': {
        u'host': u'',
        u'port': 0
    },
    u'SIT': {
        u'host': u'',
        u'port': 0
    },
    u'PROD': {
        u'host': u'',
        u'port': 0
    }
}

# oss目录配置
BUCKET_CONFIG = {
    u'DEV': u'',
    u'SIT': u'',
    u'PROD': u''
}

# 解析的topic配置
PARSE_TOPIC_CONFIG = {
    u'DEV': u'',
    u'SIT': u'',
    u'PROD': u''
}

# 入库topic配置
PROCESS_TOPIC_CONFIG = {
    u'DEV': u'',
    u'SIT': u'',
    u'PROD': u''
}

# OTS实例配置
OTS_INSTANCE_CONFIG = {
    u'DATA': {
        u'DEV': u'',
        u'SIT': u'',
        u'PROD': u''
    },
    u'CACHE': {
        u'DEV': u'',
        u'SIT': u'',
        u'PROD': u''
    }
}
