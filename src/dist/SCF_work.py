# -*- coding: utf-8 -*-

"""
TSDM-coin-farmer
适配云函数, 单个文件完成天使动漫多人打工
requests方式
cookies文件格式:
{
  "user_1": {
    "cookie_1": "value_1",
    ...
  },
  "user_2": {
    "cookie_1": "value_1",
    ...
  }
}
"""


import json
import logging
import random
import re
import sys
import time
from pathlib import Path
from typing import List

import requests

logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别为DEBUG
    format="%(asctime)s %(levelname)s %(pathname)s %(lineno)d %(message)s",  # 设置日志格式
    datefmt="%Y-%m-%d %H:%M:%S",  # 设置日期格式
    stream=sys.stdout,  # 设置输出流为sys.stdout
)


WORK_URL = "https://www.tsdm39.com/plugin.php?id=np_cliworkdz:work"
TSDM_DOMAIN = ".tsdm39.com"
TSDM_COOKIE_FILE = "tsdm_cookies.json"
GET_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7",
    "Connection": "keep-alive",
    "Host": "www.tsdm39.com",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "macOS",
}
POST_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.tsdm39.com",
    "Origin": "https://www.tsdm39.com",
    "Referer": "https://www.tsdm39.com/plugin.php?id=np_cliworkdz:work",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "macOS",
}


def get_cookies_all():
    """从文件读取所有cookies
    { username: [cookie_list] }
    """
    p = Path(TSDM_COOKIE_FILE)
    if not p.exists():
        logging.error(f"文件: {p} 不存在")
        return None
    with open(TSDM_COOKIE_FILE, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def get_cookies_by_domain(domain: str):
    """从所有cookie里分离出指定域名的cookie
    domain: cookie_list domain, (".tsdm39.com")
    """
    cookies_all = get_cookies_all()
    domain_cookies = {}

    for username in cookies_all.keys():
        curr_user_cookies = cookies_all[username]
        curr_user_cookies_domained = []

        # 同一个用户名下可能有多个网站的cookie
        for cookie in curr_user_cookies:
            if cookie["domain"] == domain:
                curr_user_cookies_domained.append(cookie)

        if curr_user_cookies_domained != []:
            domain_cookies[username] = curr_user_cookies_domained

    return domain_cookies


def work_single_post(cookies: List):
    """用post方式为一个账户打工
    cookie_list: List[Dict]
    """
    session = requests.Session()
    session.headers.update(GET_HEADERS)
    session.cookies.update(cookies)

    # 打工之前必须访问过一次网页
    res = session.get(WORK_URL)

    if "必须与上一次间隔" in res.text:
        result = re.search("您需要等待(.*)后即可进行", res.text)
        logging.info(f"该账户已经打工过{f' 需要等待{result.group(1)}' if result else ''}")
        return True

    session.headers.update(POST_HEADERS)

    counter = 0
    while True:
        res = session.post(WORK_URL, data="act=clickad")
        counter += 1
        logging.debug(f"post: {counter} times, res: {res.text}")
        try:
            work_num = int(res.text)
            if work_num == 6:
                logging.debug(f"打工完成, 共请求了 {counter} 次")
                break
            elif work_num > 6 or work_num < 0:
                logging.error(f"post WORK_URL res abnormal: {res.text}")
                return False
            else:
                wait_time = round(random.uniform(1, 2), 2)
                logging.info(f"sleep: {wait_time}s")
                time.sleep(wait_time)
        except ValueError as e:
            logging.error(f"post WORK_URL has exception: {e}\nres: {res.text}")
            return False

    res = session.post(WORK_URL, data="act=getcre")

    if "您已经成功领取了奖励天使币" in res.text:
        logging.info("打工成功")
        return True
    elif "作弊" in res.text:
        logging.error("打工失败, 作弊判定, 重试...")
    elif "请先登录再进行点击任务" in res.text:
        logging.error("打工失败, cookie失效...")
    elif "服务器负荷较重" in res.text:
        logging.error("打工失败, TSDM: 服务器负荷较重, 操作超时...")
    else:
        logging.error("======未知原因打工失败=======")
    logging.error(f"getcre res: {res.text}")

    session.close()
    return False


def work_multi_post():
    cookies = get_cookies_all()
    if not cookies:
        logging.error("读取cookies文件异常")
        return False

    all_success = True

    for user in cookies.keys():
        logging.info(f"正在打工, user: {user}")
        try:
            if work_single_post(cookies[user]):
                logging.info(f"user: {user}, 打工完成")
            else:
                logging.error(f"user: {user}, 打工失败")
                all_success = False
        except Exception as e:
            logging.error(f"user: {user}, 抛出异常: {e}")
            all_success = False

    return all_success


def main_handler(event, context):
    return work_multi_post()
