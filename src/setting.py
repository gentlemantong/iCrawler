# -*- coding: utf-8 -*-
PROJECT_SETTING = {
    u'COMMON': {
        u'class': u'',  # module名要和类名相同
        u'pipeline': u'',  # module名要和类名相同
        u'priority': 500,  # 数字越小优先级越高

        u'source': u'kafka',  # 消息来源，[static,kafka,mongodb,mysql,excel,csv]
        u'loop': True,  # 是否循环
        u'source_encode': u'UTF-8',  # 数据源编码，目前只有当source为CSV时才用到

        # 当source为kafka时，需指定这两个参数
        u'kafka_topic': u'',  # kafka消息队列的topic
        u'kafka_group': u'',  # kafka消息队列的group

        # 当source为 mysql|mongodb 时需要指定这四个参数
        u'db_service': True,  # 是否使用接口服务
        u'db_service_env': None,  # 服务环境 - 为None时则使用config文件中的配置
        u'db_schema': u'',  # 数据库连接模式
        u'db_table': u'',  # 数据表
        u'db_limit': 100,  # 单次查询最大数量
        u'db_keys': [],  # 需要获取的键
        u'db_filter': {u'$e': {}, u'$ne': {}, u'$lt': {}, u'$lte': {}, u'$gt': {}, u'$gte': {}},  # 筛选条件

        # 当source为static时需要将消息内容手动传入改参数，单条消息必须为一个dict
        u'messages': [],  # 手动上传消息列表

        u'run_schema': u'always',  # always|repeat
        u'valid_time': [  # 只有当run_schema为repeat时才会生效
            u'1/23:00-1/23:00', u'2/23:00-2/23:00', u'3/23:00-3/23:00', u'4/23:00-4/23:00', u'5/23:00-5/23:00',
            u'6/23:00-6/23:00', u'7/23:00-7/23:00'
        ]
    },
    u'PLUGINS': {
        u'STATIC': [  # 配置
            {
                u'class': u'src.plugins.qiye.job.BaiduJobProcessor',
                u'pipeline': u'src.pipelines.qiye.job.JobPipeline',
                u'priority': 498,
                u'kafka_topic': u'topic_qy_auto_update',
                u'kafka_group': u'qy_jobs'
            },  # 招聘数据自动更新
        ],
        u'TODO': [
        ],
        u'CRAWLER00': [
            {
                u'class': u'src.plugins.qiye.job.BaiduJobProcessor',
                u'pipeline': u'src.pipelines.qiye.job.JobPipeline',
                u'priority': 498,
                u'kafka_topic': u'topic_qy_auto_update',
                u'kafka_group': u'qy_jobs'
            },  # 招聘数据自动更新
        ]
    }
}
