# -*- coding: utf-8 -*-

"""
TSDM-coin-farmer
适配云函数, 单个文件完成天使动漫多人签到
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

from datetime import datetime
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

# ======== CONSTANT ========
SIGN_URL = "https://www.tsdm39.com/plugin.php?id=dsu_paulsign:sign"
SIGN_POST_PARAMS = "&operation=qiandao&infloat=1&inajax=1"
SIGN_FORM_PARAMS = "formhash={formhash}&qdxq=ym&qdmode=3&todaysay=&fastreply=1"
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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Length": "56",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.tsdm39.com",
    "Origin": "https://www.tsdm39.com",
    "Referer": "https://www.tsdm39.com/plugin.php?id=dsu_paulsign:sign",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
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


# ======= SIGN ======
sign_page_with_param = "https://www.tsdm39.com/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=1"


def sign_single_post(cookies: List):
    """用post方式为一个账户签到
    cookies: List[{k: v}]
    """
    session = requests.Session()
    session.headers.update(GET_HEADERS)
    session.cookies.update(cookies)

    res = session.get(SIGN_URL)

    if res.status_code != 200:
        logging.error(f"签到失败, res.status_code: {res.status_code}")
        logging.error(f"res.text: {res.text}")
        return False

    result = re.search('formhash=(.*)"', res.text)
    if not result:
        logging.error(f"签到失败, 无法获取formhash")
        logging.error(f"res.text: {res.text}")
        return False

    formhash = result.group(1)
    logging.debug(f"formhash: {formhash}")

    sign_form_data = SIGN_FORM_PARAMS.format(formhash=formhash)
    logging.debug(f"sign_form_data: {sign_form_data}")

    session.headers.update(POST_HEADERS)

    sign_response = session.post(SIGN_URL + SIGN_POST_PARAMS, data=sign_form_data)

    if "获得随机奖励" in sign_response.text:
        result = re.search("获得随机奖励 (.*) \. </div>", res.text)
        logging.info(f"签到成功 {f'{result.group(1)}' if result else ''}")
        return True
    elif "您今日已经签到" in sign_response.text:
        logging.info("该账户已经签到过")
        return True

    if "已经过了签到时间段" in sign_response.text or "签到时间还没有到" in sign_response.text:
        logging.error("签到失败: 目前不在签到时间段")
    elif "未定义操作" in sign_response.text:
        logging.error(f"签到失败, 可能是formhash获取错误")
    else:
        logging.error("======未知原因签到失败=======")
    logging.error(f"sign res: {sign_response.text}")

    session.close()
    return False


def sign_multi_post():
    cookies = get_cookies_all()
    if not cookies:
        logging.error("读取cookies文件异常")
        return False

    all_success = True

    for user in cookies.keys():
        logging.info(f"正在签到, user: {user}")
        try:
            if sign_single_post(cookies[user]):
                logging.info(f"user: {user}, 签到完成")
                time.sleep(random.uniform(0.5, 1))
            else:
                logging.error(f"user: {user}, 签到失败")
                all_success = False
        except Exception as e:
            logging.error(f"user: {user}, 抛出异常: {e}")
            all_success = False

    return all_success


def main_handler(event, context):
    return sign_multi_post()
