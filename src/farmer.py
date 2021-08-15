from datetime import datetime
import schedule
from actions import *


def heartbeat():
    print("heartbeat: ", datetime.now())


def work_all():
    print(time.time(), "正在打工.......")
    work_multiple()


def sign_all():
    print(time.time(), "正在签到.......")
    sign_multiple()


if __name__ == '__main__':
    print("正在运行计划任务: heartbeat=30min")
    schedule.every(30).minutes.do(heartbeat)
    schedule.every(365).minutes.do(work_all)  # 6hr + 5min
    schedule.every().day.at("10:30").do(sign_all)  # 每天 10:30 签到

    while True:
        schedule.run_pending()  # 运行所有可以运行的任务
        time.sleep(10)
