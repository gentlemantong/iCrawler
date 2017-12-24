# iCrawler
A simple web crawler.

### 1. 数据流向图
Provider从外部（Kafka, MySQL, MongoDB, Excel, CSV等）获取消息，发送给Processor处理（数据抓取, 数据清洗等）；
Processor处理完之后将结果发送给Pipeline做后续持久化相关操作（入库, Kafka, 本地文件等）。


### 2. 架构
- 启动脚本加载配置文件，启动调度器程序（调度器负责协调Provider, Processor和Pipeline）。
- Provider, Processor和Pipeline分别使用三个独立的协程工作。
    - 根据配置, Provider不断从指定的外部数据源获取消息，通过queue发送给Processor处理；
    - Processor从queue中获取自己需要执行的消息体，执行抓取、解析、清洗等相关操作，然后将处理结果通过queue发送给Pipeline处理；
    - Pipeline从queue中获取自己需要操作的数据对象，执行后续持久化相关操作；


### 3. 涉及到的Python相关模块
- Python版本：2.7.X(兼容3.6.X)
- 相关模块：
`gevent`, `magic`, `requests`, `pymysql`, `bson`, `pymongo`, `xlrd`, `xlwt`, `cchardet`, `bs4`, `lxml`等（因为数据库、Kafka和阿里相关服务主要是调用http服务，省去了很多自己封装方法的麻烦，所以很多的包在这里都没有用到，比如阿里的ots2等）。
- 编辑器：推荐使用PyCharm

### 4. 目录结构（示例）
 
#### 4.0 cache：临时文件存放目录
当Provider从外部（Kafka等）获取消息时，为防止在运行过程中突然出现中断导致的消息体丢失，Provider会将消息体以临时文件的形式存储在本地的cache目录下（pickle）。在数据处理结束后，程序会自动删除缓存的临时文件。

#### 4.1 logs：日志文件存放目录
框架的日志文件默认存储在logs文件夹下。
日志文件的命名格式为：`iCrawler_{0}.log`，其中参数为对应Schema的值（schema会在后面介绍）。
日志文件目前默认只保存1个备份（1个小时之前的备份）

#### 4.2 src：项目文件主体
src目录是项目文件的主体。当我们开始一个新的任务时，需要执行的所有操作中，99%都在该目录进行。
##### 4.2.0 cores：Scheduler相关文件

cores是调度器相关的核心代码文件目录。所有的任务代码在运行时，都是这些文件进行调度的，这里只简单介绍一下各个文件的作用（无特殊需求，不需要修改该部分的代码）
###### 4.2.0.0 services：封装的相关服务调用
- `dama.py`：打码相关服务，目前仅支持图形类验证码，封装了包括打码兔和我们自己部署的打码服务；
- `dama2_client.py`：封装的打码兔服务（正常不需要直接调用该文件中的方法，`dama.py`已经对该文件进行了二次封装，可以直接调用dama.py）；
- `duplicate_client.py`：查重；
- `excel_client.py`：excel基本操作；
- `http_client.py`：网络请求相关方法；
- `kafka_client.py`：二次封装的kafka调用方法（调用http服务）；
- `mongodb_client.py`：mongodb相关方法（包括直连和调用http服务两种方式）；
- `mysql_client.py`：mysql相关方法（包括直连和调用http服务两种方式）；
- `oss_client.py`：二次封装的阿里OSS相关操作方法（调用http服务）；
- `proxy_client.py`：二次封装的代理相关方法（调用http服务）；
###### 4.2.0.1 `customer.py`：自定义类，目前只定义了`CustomerJsonEncoder`，用来给`json.dumps`使用
###### 4.2.0.2 `exception.py`：异常类
###### 4.2.0.3 `item.py`：结果类的父类
###### 4.2.0.4 `launcher.py`：启动器，为对应的provider，processor和pipeline创建自己的协程
###### 4.2.0.5 `pipeline.py`：各个Pipeline的父类以及调度方法
###### 4.2.0.6 `process.py`：各个Processor的父类以及调度方法
###### 4.2.0.7 `provider.py`：Provider主体及调度方法

##### 4.2.1 items：结果类目录

 该目录主要存放每个维度数据的结果类文件。结果类文件的作用是确保每个维度数据在执行过程中保持结构一致，当然，加上合理的注释后也可以作为文档使用。
下面是一个常见的结果类定义格式：
```python
# -*- coding: utf-8 -*-


class JSGSJNewlyItem(object):
    """江苏省新增企业公告结果类"""

    __slots__ = (
        u'company',         # 企业名称
        u'number',          # 企业注册号
        u'legal_rep',       # 法定代表人（负责人）
        u'address',         # 企业住所
        u'type',            # 企业类型
        u'date',            # 新设日期
        u'url'              # 详情页链接
    )

    def __init__(self):
        self.company = None
        self.number = None
        self.legal_rep = None
        self.address = None
        self.type = None
        self.date = None
        self.url = None
```
结果类文件在调用部分代码如下：
```python
# -*- coding: utf-8 -*-
from JSGSJNewlyItem import JSGSJNewlyItem

item = JSGSJNewlyItem()
item.company = u'苏宁易购'
item.number = u'123456'
...
```

##### 4.2.2 piplines：Pipeline类目录

该目录主要存放各个维度数据的结果pipeline类文件。 pipeline类文件主要进行数据持久化的相关操作，也可以进行结果的处理和过滤等。下面是常见的pipeline类结构：
```python
# -*- coding: utf-8 -*-
import uuid

from src.config import BUCKET_CONFIG, BUCKET_SCHEMA, PARSE_TOPIC_SCHEMA, PARSE_TOPIC_CONFIG
from src.cores.pipeline import 
from src.cores.pipeline import Pipeline


class ExecutedPersonPipeline(Pipeline):

    def __init__(self):
        super(ExecutedPersonPipeline, self).__init__()
        self.bucket = BUCKET_CONFIG[BUCKET_SCHEMA]
        self.folder = u'qy_execute_person'
        self.kafka = PARSE_TOPIC_CONFIG[PARSE_TOPIC_SCHEMA]

    def process_item(self, config, result):
        """
        处理数据
        :param config: 配置
        :param result: 数据
        :return: 无
        """
        self.transfer_none_to_empty_str(result)
        if not result.get(u'keyword'):
            result[u'keyword'] = u',,'
        if result.get(u'caseCode'):
            filename = str(uuid.uuid4())
            result[u'_type'] = self.folder
            # 构造流向卡夫卡的数据
            kafka_record = {
                u'keyword': result[u'keyword'],
                u'_traceid': result.get(u'_traceid'),
                u'_dataid': filename,
                u'_sent_time': result.get(u'_sent_time'),
                u'_type': result[u'_type']
            }
            # 数据流向OSS和卡夫卡
            self.flow_to_oss_and_kafka(self.bucket, self.folder, filename, result, self.kafka, kafka_record)
```
其中：
- 该类实现了将抓取结果发送到OSS和Kafka队列的功能；
- `ExecutedPersonPipeline`类继承了`Pipeline`类（父类）；
- `process_item(self, config, result)`方法必须进行重构（父类中的该方法为空），且需要以该函数为起始函数，编写主处理逻辑；
- `transfer_none_to_empty_str`和`flow_to_oss_and_kafka`也是继承自父类。正常情况下，父类中的方法除了`process_item`需要重构外，其他方法都只需要直接调用使用即可（类似工具类方法）；

##### 4.2.3 plugins：Processor类目录

plugins目录是存放processor类的地方，也是通常我们编写一个爬虫或清洗脚本的主要目录。下面是一个常规爬虫的代码编写样例：
```python
# -*- coding: utf-8 -*-
import logging
import re

import gevent
from bs4 import BeautifulSoup

from src.cores.exceptions import NoDataException
from src.cores.process import Processor
from src.cores.services import http_client
from src.items.qiye.fund.black_list.BlackListItem import BlackListItem


class BlackListProcessor(Processor):
    """违反自律规则黑名单数据采集"""

    def __init__(self, config, result_queue):
        super(BlackListProcessor, self).__init__(config, result_queue)

    def request_list_page(self, message, page_no):
        """
        处理消息
        :param message: 消息
        :param page_no: 页码
        :return: 最大页码 | 列表页数据集合 | 结果类 | 是否有详情页
        """
        max_page_no = 1
        list_records = []
        has_detail = False

        url = u'http://www.amac.org.cn/xxgs/hmd/'
        err_count = 0
        while err_count < self.retry_limit:
            try:
                self.refresh_proxy()
                resp_text = (http_client.do_http_get(
                    url=url,
                    headers=self.base_headers,
                    cookies=self.base_cookies,
                    proxies=self.base_proxies
                ))[0]
                if resp_text:
                    max_page_no = self.__parse_list_page(list_records, resp_text)
                    has_detail = True
                    break
                else:
                    raise NoDataException(u'Empty response!')
            except NoDataException as nde:
                logging.exception(u'Exception!')
                self.base_proxies = None
            except Exception as e:
                logging.exception(u'Exception!')
                break
            err_count += 1
            gevent.sleep(1)

        return max_page_no, list_records, BlackListItem, has_detail

    @staticmethod
    def __parse_list_page(list_records, resp_text):
        """
        解析列表页
        :param list_records: 数据集合
        :param resp_text: 列表页页面数据
        :return: 最大页码
        """
        max_page_no = 1
        pattern = re.compile(u'\d+页')
        matches = pattern.findall(resp_text)
        if matches:
            max_page_no = int(matches[0].replace(u'页', u'').strip())

        soup = BeautifulSoup(resp_text, u'lxml')
        links = soup.find_all(u'a', attrs={u'href': re.compile(r'\.\./\.\./xxgs/hmd/\d+\.shtml')})
        for link in links:
            item = BlackListItem()
            item.url = u'http://www.amac.org.cn' + link[u'href'].replace(u'../..', u'')
            list_records.append(item)
        return max_page_no

    def request_detail_page(self, args):
        """
        请求详情页
        :param args: 参数的集合
        :return: 无
        """
        message, record, record_cls = args

        err_count = 0
        while err_count < self.retry_limit:
            try:
                self.refresh_proxy()
                resp_text = (http_client.do_http_get(
                    url=record.url,
                    headers=self.base_headers,
                    cookies=self.base_cookies,
                    proxies=self.base_proxies
                ))[0]
                if resp_text:
                    self.__parse_detail_page(message, record, record_cls, resp_text)
                    break
                else:
                    raise NoDataException(u'Empty response!')
            except NoDataException as nde:
                logging.exception(u'Exception!')
                self.base_proxies = None
            except Exception as e:
                logging.exception(u'Exception!')
                break
            err_count += 1
            gevent.sleep(1)

    def __parse_detail_page(self, message, record, record_cls, resp_text):
        """
        解析详情页
        :param message: 查询消息
        :param record: 结果对象实例
        :param record_cls: 结果类
        :param resp_text: 详情页页面数据
        :return: 无
        """
        soup = BeautifulSoup(resp_text, u'lxml')
        # 公布时间
        publish_date = None
        ld_date = soup.find(u'div', attrs={u'class': u'ldDate'})
        if ld_date:
            publish_date = ld_date.get_text().replace(u'日期：', u'').strip()

        table = soup.find(u'div', attrs={u'class': u'ldContent'})
        if not table:
            return
        rows = table.find_all(u'tr')
        if len(rows) < 2:
            return
        for i, v in enumerate(rows):
            if i == 0:
                continue
            columns = v.find_all(u'td')
            if len(columns) == 3:
                record.punish_date = columns[0].get_text().strip()
                record.company = columns[1].get_text().strip()
                record.punish_no = columns[2].get_text().strip()
                if columns[2].find(u'a'):
                    record.punish_file = columns[2].find(u'a')[u'href']
                record.publish_date = publish_date
                self.pipeline_pusher(message, record, record_cls)
            elif len(columns) == 4:
                record.punish_date = columns[0].get_text().strip()
                record.person = columns[1].get_text().strip()
                tags = columns[2].find_all(u'p')
                if len(tags) == 2:
                    record.company = tags[0].get_text().strip()
                    record.job = tags[1].get_text().strip()
                record.punish_no = columns[3].get_text().strip()
                if columns[3].find(u'a'):
                    record.punish_file = columns[3].find(u'a')[u'href']
                record.publish_date = publish_date
                self.pipeline_pusher(message, record, record_cls)
```
其中：
- 该类实现了列表页和详情页的抓取（`request_list_page`和`request_detail_page`方法）和解析（`__parse_list_page`和`__parse_detail_page`方法）；
- `BlackListProcessor`类继承了`Processor`类（父类）；
- 新建一个processor类时，需要注意以下几点：
    - 确保`Processor`类是新类的一个父类（不一定是直接父类），这样新的类才能正常执行；
    - 新类的`__init__`方法必须初始化父类的`__init__`方法（参照上面代码）；
    - 新类必须重构`request_list_page`方法（该方法既是父类默认的列表页抓取函数，也是开始新类抓取或处理的入口）；
    - 列表页数据结果存放在`request_list_page`的返回参数 - `list_records`中；
    - 列表页最大页码通过`max_page_no`传出，父类会自动进行翻页；
    - 如果新的爬虫类需要抓取详情页，则`request_list_page`方法返回的参数之一的`has_detail`需要为`True`，并且`list_records`必须是有效的（不能为空）；
    - 如果**只需要抓取列表页**，将列表页数据放到对应的item实例中，添加到`list_records`。`has_detail`设为`False`，父类会自动将抓取结果发送给对应的`pipeline`类处理；
    - 如果需要抓取详情页，需要将列表页数据放到`list_records`，`has_detail`设为`True`。然后重构`request_detail_page`方法，父类会将列表页数据自动传递到该方法。记住，抓取详情页的话，需要手动调用父类的`pipeline_pusher`方法，将结果发送给对应的pipeline类处理；
- 前面定义的item类在这里被使用；

##### 4.2.4 utils：工具类目录
该目录主要存放一些工具类。工具类可以根据任务需求进行添加和修改。

##### 4.2.5 `config.py`：参数配置文件
config文件主要是一些运行参数的配置，通常不需要更新该文件。

##### 4.2.6 requirements：依赖包目录
`requirements`是为了方便新环境安装依赖包添加的文件。正常在新的环境下，在安装好相应的python之后，进入该目录，执行
```sh
pipX install -r requirements
```
其中`pipX`是与需要使用的python对应的`pip`命令。（安装过程如果需要加速，可使用`pipX install -r requirements -i https://mirrors.aliyun.com/pypi/simple/`）

##### 4.2.7 setting.py：启动配置文件

setting是使用json格式编写的配置文件。项目启动时，程序加载指定的schema（schema是`lauch.py`的一个参数，值为上图中`PLUGINS`的一个键名，如`STATIC`，`CRAWLER00`等。运行时，每个进程只能指定一个schema。如果需要开启不同的schema，则需要开启不同的进程）下的插件，运行程序。

###### 4.2.7.0. COMMON：默认配置参数
`COMMON`字段是单个插件可配置参数的字段库，同时也初始化了配置参数。正式部署时，单个插件需要根据任务需求选择对应的参数，并配置合适的值。
```python
u'COMMON': {
    u'class': u'',                          # module名要和类名相同
    u'pipeline': u'',                       # module名要和类名相同
    u'priority': 500,                       # 数字越小优先级越高

    u'source': u'kafka',                    # 消息来源，[static,kafka,mongodb,mysql,excel,csv]
    u'loop': True,                          # 是否循环
    u'source_encode': u'UTF-8',             # 数据源编码，目前只有当source为CSV时才用到

    # 当source为kafka时，需指定这两个参数
    u'kafka_topic': u'',                    # kafka消息队列的topic
    u'kafka_group': u'',                    # kafka消息队列的group

    # 当source为 mysql|mongodb 时需要指定这四个参数
    u'db_service': True,                    # 是否使用接口服务
    u'db_service_env': None,                # 服务环境 - 为None时则使用config文件中的配置
    u'db_schema': u'',                      # 数据库连接模式
    u'db_table': u'',                       # 数据表
    u'db_limit': 100,                       # 单次查询最大数量
    u'db_keys': [],                         # 需要获取的键
    u'db_filter': {u'$e': {}, u'$ne': {}, u'$lt': {}, u'$lte': {}, u'$gt': {}, u'$gte': {}},        # 筛选条件

    # 当source为static时需要将消息内容手动传入改参数，单条消息必须为一个dict
    u'messages': [],                        # 手动上传消息列表

    u'run_schema': u'always',               # always|repeat
    u'valid_time': [                        # 只有当run_schema为repeat时才会生效
        u'1/23:00-1/23:00', u'2/23:00-2/23:00', u'3/23:00-3/23:00', u'4/23:00-4/23:00', u'5/23:00-5/23:00',
        u'6/23:00-6/23:00', u'7/23:00-7/23:00'
    ]
},
```
- class：插件processor类的相对路径，如`src.plugins.qiye.executed_person.ExecutedPersonProcessor`。需要注意的是，类文件的名称需要与具体的类名相同，如类文件为`ExecutedPersonProcessor.py`，其类名为`ExecutedPersonProcessor`。
- pipeline：插件pipeline类的相对路径，如`src.pipelines.qiye.executed_person.ExecutedPersonPipeline`。和`class`参数一样，module名要和类名相同。
- priority：插件的优先级，数字越小，优先级越高。需要注意的是，目前框架的优先级规则比较简单 - 只要队列中有高优先级的消息体，那么低优先级的消息就不会被处理。这在使用的使用后需要注意。
- source：插件的消息来源。目前支持[static,kafka,mongodb,mysql,excel,csv]，其中：
    - static：静态消息。本地调试时使用，通常会搭配`messages`参数一起使用；
    - kafka：kafka队列。使用该参数时，需要配置`kafka_topic`和`kafka_group`；
    - mongodb：mongodb数据库。使用该参数时，需要配置`db_service`，`db_service_env`，`db_schema`，`db_table`，`db_limit`，`db_keys`和`db_filter`；
    - mysql：mysql数据库。使用该参数时，需要配置`db_service`，`db_service_env`，`db_schema`，`db_table`，`db_limit`，`db_keys`和`db_filter`；
    - excel：Excel文件。使用该参数时，需要将文件的相对路径陪在`messages`中；
    - csv：CSV文件。使用该参数时，需要将文件的相对路径陪在`messages`中；
- loop：是否循环读取数据源。改参数支队可循环读取的消息来源有效，比如`static`，`mongodb`，`mysql`，`excel`和`csv`，对`kafka`，`redis`这类消息队列无效；
- source_encode：数据源编码，目前只有当source为CSV时才用到；
- kafka_topic：kafka队列的topic。配合source值为`kafka`时使用；
- kafka_group：kafka队列的group。配合source值为`kafka`时使用；
- db_service：是否使用接口服务。配合source值为`mongodb`或`mysql`时使用；
- db_service_env：若db_service为`True`，可设置该参数（值可为`LOCALHOST`，`SIT`，`PROD`）。若不配置（即值为`None`），则默认使用`config.py`中的`__ENVIRONMENT`配置；
- db_schema：数据库模式名。配合source值为`mongodb`或`mysql`时使用；
- db_table：需要访问的数据表名。配合source值为`mongodb`或`mysql`时使用；
- db_limit：每次获取数据的最大数量。配合source值为`mongodb`或`mysql`时使用，值为数字；
- db_keys：需要获取的参数。配合source值为`mongodb`或`mysql`时使用，值为参数名列表；
- db_filter：筛选条件。配合source值为`mongodb`或`mysql`时使用，根据需要选择对应的筛选条件；
- messages：当source为`static`，`excel`或`csv`时，需要配置该字段，值为消息体或文件名列表。
当`source`为`static`时，该参数为静态消息体列表，示例：
```python
{
    u'class': u'src.plugins.gongshang.qxb.app.NegativeProcessor',
    u'pipeline': u'src.pipelines.gongshang.qxb.app.AppPipeline',
    u'source': u'static',
    u'loop': False,
    u'messages': [
        {
            u'keyword': u'山东天鸿模具股份有限公司,370635228062140,9137060077315495XC',
            u'company': u'山东天鸿模具股份有限公司',
            u'reg_no': u'370635228062140',
            u'credit_no': u'9137060077315495XC',
            u'eid': u'',
            u'org_eid': u'fc82ba18-7db6-4f1e-92aa-4076fb389663',
            u'_traceid': u'123456789',
            u'_sent_time': u'2017-10-20 19:28:00'
        }
    ]
},  # APP获取企业知识产权信息 - 批量更新专利数大于1000的企业
```
当source为`excel`或`csv`时，该参数为文件名列表，示例：
```python
{
    u'class': u'src.plugins.pusher.personal_names.PersonalNamesPusher',
    u'pipeline': u'src.pipelines.pusher.personal_names.PersonalNamesPipeline',
    u'source': u'csv',
    u'loop': False,
    u'messages': [u'cache/person_name.csv']
},  # 人名发送脚本
```
- run_schema：程序运行模式。
    - `always`：一直运行；
    - `repeat`：定时重复。此时需要配合`valid_time`使用；
- valid_time：有效运行时间段列表。只有当run_schema为repeat时才会生效。下面的示例配置表示每周一和周三的20:00~23:00运行插件
```python
u'valid_time': [                        # 只有当run_schema为repeat时才会生效
    u'1/20:00-1/23:00', u'3/20:00-3/23:00',
]
```

###### 4.2.7.1. PLUGINS：插件列表
PLUGINS是插件的列表，更确切地说是插件schema的列表。具体的插件配置是在各个schema下，可以根据任务需求增加新的schema或去掉不用的schema。
默认情况下，`STATIC`和`TODO`这两个schema不会参与正式环境运行，也不能删掉。其他的schema，可根据部署的需要，添加、删除或移动其中的插件配置（只改动自己开发的插件配置）。
- `STATIC`是本地开发时默认使用的schema，比如在本地开发和调试企业负面信息抓取，setting的调试配置如下：

该配置的含义如下：
    - 使用`src.plugins.gongshang.qxb.app.NegativeProcessor`文件（python中引用模块不需要加.py）中的`NegativeProcessor`类作为当前插件的processor；
    - 使用`src.pipelines.gongshang.qxb.app.AppPipeline`文件中的`AppPipeline`类作为当前插件的pipeline；
    - 使用静态消息。静态消息配置在`messages`中；
    - 不用循环；
- `TODO`是一些开发好尚未部署的插件配置
- 正式部署时，将需要部署的插件配置到需要开启的schema下面。如下图，线上需要部署*贵州省新增企业公告抓取*，*被执行人自动更新*和*失信被执行人自动更新*这三个插件，则需要将这三个插件的配置放到`CRAWLER00`下面。


#### 4.3 launch.py：启动文件
```python
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
```
`launch.py`文件代码比较简单，主要是使用传入的参数启动整个框架。
- 可传入的启动参数有三个，说明如下：
    - `--schema`：对应需要启动的`setting.py`中的`PLUGINS`的一个参数；
    - `--log_level`：日志级别；
    - `--task`：并发量。分别为procrssor和pipeline开启多少协程，数值越大，并发越高；
- 在开发环境，该文件无需修改，在配置好`setting.py`下`STATIC`这个schema之后，直接右键-Run/debug即可；
- 在服务器上，使用对应的`sh`文件启动，尽量不要直接手动输入参数运行；

#### 4.4 crawler00.sh：部署启动脚本
在Linux服务器上使用该类脚本启动框架（需要事前设置`sh`文件为可执行文件）。
```sh
#!/bin/sh
python27 launch.py --schema CRAWLER00 --task 20 --log_level debug
```
其中：
- 通常文件名对应需要启动的schema的小写。比如，`crawler00.sh`表示启动的是`CRAWLER00`这个schema下面的插件；
- 事先需要在对应的服务器上配置好可执行的`python27`命令才行；
- 传入的参数分别对应`launch.py`的三个参数；

###5. 项目路径
DEV：svn://114.55.126.4:10012/pub/data/DEV/iCrawler
SIT：svn://114.55.126.4:10012/pub/data/SIT/iCrawler
PROD：svn://114.55.126.4:10012/pub/data/spider/others/iCrawler

### 6. 插件开发几步走
1. 新增插件
通常，一个新维度数据的爬虫需要新建3个文件：item文件（根据任务情况建在items下面的对应层级目录中），processor文件（建在plugins下）和pipeline文件（建在pipelines下）。

2. 配置setting；
开发阶段，可以仿照【4.2.7】相关示例，配置在`STATIC`中。

3. 本地开发测试；
代码编写和调试。

4. SIT测试；
本地测试成功后，将`STATIC`中的配置放到某个schema下，并修改参数为正式运行时的配置，merge代码到SIT环境，进行测试。

5. 正式部署；
SIT测试成功，Code Review通过之后，可以将代码和配置merge到PROD环境进行部署。
部署后观察运行正常，整个开发流程结束。
