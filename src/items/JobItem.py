# -*- coding: utf-8 -*-
from baseitem import BaseItem, Type


class JobItem(BaseItem):
    """招聘数据结果类"""
    # 职位名称
    title = Type(data_type=str)
    # 薪资
    salary = Type(data_type=str)
    # 所在省份
    province = Type(data_type=str)
    # 所在城市
    city = Type(data_type=str)
    # 所在地区
    district = Type(data_type=str)
    # 所在地详细地址
    location = Type(data_type=str)
    # 位置
    position = Type(data_type=str)
    # 年龄
    age = Type(data_type=str)
    # 性别
    sex = Type(data_type=str)
    # 学历要求
    education = Type(data_type=str)
    # 经验要求
    years = Type(data_type=str)
    # 招聘人数
    number = Type(data_type=str)
    # 来源
    source = Type(data_type=str)
    # 资质
    qualification = Type(data_type=str)
    # 全职 / 兼职
    job_type = Type(data_type=str)
    # 职位类型
    job_class = Type(data_type=str)
    # 发布日期
    date = Type(data_type=str)
    # 有效日期
    end_date = Type(data_type=str)
    # 职责描述
    description = Type(data_type=str)
    # 福利清单
    welfare_list = Type(data_type=list, child_type=str)
    # 所属部门
    department = Type(data_type=str)
    # 公司名称
    name = Type(data_type=str)
    # eid
    eid = Type(data_type=str)
    # 公司所属行业
    ent_ind = Type(data_type=str)
    # 公司规模
    size = Type(data_type=str)
    # 公司类型
    ent_type = Type(data_type=str)
    # 公司描述
    ent_desc = Type(data_type=str)
    # 企业链接
    ent_url = Type(data_type=str)
    # 企业logo
    ent_logo = Type(data_type=str)
    # 企业简称
    ent_short_name = Type(data_type=str)
    # 联系邮箱
    email = Type(data_type=str)
    # 源链接
    url = Type(data_type=str)
