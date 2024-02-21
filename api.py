# api.py
import copy
import json
import logging
import time

import requests

# noinspection PyUnresolvedReferences
import log
from config import Config

# 全局变量
config = Config()


def get_tasks_list():
    url = "/api/task/list"
    data = {"platform": "android", "client": "app", "sign": "", "ver_name": "0.11.47", "ver_code": 187, "gz": 0}
    response = request_api(url, data)
    return response


def coin_use(aid):
    url = "/api/coin/use"
    data = {"goods_id": 2, "params": aid, "price": 1, "number": 10, "total_price": 10}
    response = request_api(url, data)
    if response:
        logging.info(f"投币成功")
    else:
        logging.error(f"投币失败")
    return response


def get_user_info(uid):
    url = "/api/user/info"
    data = {"uid": uid}
    response = request_api(url, data)
    return response


def get_article_by_cate(page):
    url = "/api/category/get-article-by-cate"
    data = {"parent_gid": 1, "gid": 0, "page": page}
    response = request_api(url, data)
    if response:
        logging.info(f"获取第{page}页文章成功")
        return response['list']
    else:
        logging.error(f"获取第{page}页文章失败")
        return None


# noinspection PyUnusedLocal
def share_article(aid):
    task_complete(5)


def get_target_article():
    def_page, def_order = 5783, 19
    user = config.get('user')
    page, order = user.get("page", def_page), user.get('order', def_order)

    article_list = get_article_by_cate(page)
    try_time_limit = 20
    try_time = 0
    if article_list:
        # 循环点赞，直到点赞任务完成
        # order递减, page递减
        # 先测试点赞再更改page和order
        while True:
            time.sleep(1)  # 防止请求过快
            article_id = article_list[order]['aid']
            done = article_like(article_id)
            status = task_complete(3)[0] if done else False
            # 更改page和order
            if order == 0:
                page -= 1
                order = 19
            else:
                order -= 1

            # 如果任务完成，返回文章id ；如果尝试次数超过限制，返回默认文章id
            if status or try_time > try_time_limit:
                user['page'], user['order'] = page, order
                logging.error(f"尝试次数超过限制") if not status else None
                return article_id

            try_time += 1


def task_complete(id_):
    """
    完成任务，返回是否成功和消息
    
    内部打印硬币和经验值info
    :param id_: 任务id 
    :return: 是否成功，消息
    """
    # 任务id到名字的映射
    id_task_map = {
        1: "阅读一篇帖子",
        2: "收藏一篇帖子",
        3: "为一篇帖子点赞",
        5: "分享一篇帖子",
        6: "为一篇帖子投币",
        7: "完成全部任务",
        8: "签到"
    }

    url = "/api/task/complete"
    data = {"id": id_}
    response = request_api(url, data)
    if response:
        msg = (f"任务【{id_task_map[id_]}】完成🎉"
               f"获得💰{response['coin']} 🌟{response['exp']}")
        logging.info(msg)
        return True, msg
    else:
        msg = f"任务【{id_task_map[id_]}】失败⚠️"
        logging.error(msg)
        return False, msg


def article_like(aid):
    url = "/api/article/like"
    data = {"aid": aid}
    response = request_api(url, data)
    if response:
        logging.info(f"点赞文章{aid}成功")
        return True
    else:
        logging.error(f"点赞文章{aid}失败")
        return False


def add_collection(aid):
    url = "/api/history/add-collection"
    data = {"fid": aid, "class": 1}
    response = request_api(url, data)
    if response:
        logging.info(f"收藏文章{aid}成功")
    else:
        logging.error(f"收藏文章{aid}失败")
    return response


def del_collection(aid):
    url = "/api/history/del-collection"
    data = {"fid": aid, "class": 1}
    response = request_api(url, data)
    if response:
        logging.info(f"取消收藏文章{aid}成功")
    else:
        logging.error(f"取消收藏文章{aid}失败")
    return response


def add_article_history(aid):
    url = "/api/history/add-history"
    data = {"fid": aid, "class": 1}
    response = request_api(url, data)
    if response:
        logging.info(f"添加文章{aid}到历史记录成功")
    else:
        logging.error(f"添加文章{aid}到历史记录失败")
    return response


def del_article_history(aid):
    url = "/api/history/del-history"
    data = {"fid": aid, "class": 1}
    response = request_api(url, data)
    if response:
        logging.info(f"删除历史记录文章{aid}成功")
    else:
        logging.error(f"删除历史记录文章{aid}失败")
    return response


def get_user_login(data):
    url = "/api/user/login"
    response = request_api(url, data)
    if response:
        logging.info("获取security_key成功")
    else:
        logging.error("获取security_key失败")
    return response['security_key'], response['uid']


def get_user_liteInfo():
    user = config.get('user')
    user_info = get_user_info(user.get('uid'))
    if not user_info:
        logging.error("获取用户信息失败⚠️")
        return None
    nickname, coin, exp = user_info['nickname'], user_info['balance']['coin'], user_info['level']['exp']
    return {
        "nickname": nickname,
        "coin": coin,
        "exp": exp
    }


def request_api(url, data, method="POST"):
    """
    请求失败 / 返回错误，内部打印错误log
    :return: 返回数据，失败返回None
    :rtype: dict
    :param url: 请求的URL。
    :param data: 请求的数据，将被转换为JSON格式。
    :param method: HTTP请求方法，默认为"POST"。
    """
    host = config.get('host')
    if not host or host == "":
        logging.error("host为空")
        raise Exception("host为空")
    headers = config.get_headers()
    data = get_json_payload(data)

    retry_times = 3
    response = None
    for _ in range(retry_times):
        try:
            response = requests.request(method, host + url, headers=headers, data=data)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            logging.error("请求url: %s 出错⚠️\n 数据: %s\n 错误信息: %s", url, data, e)
            if _ == retry_times - 1:
                return None
            time.sleep(1)

    body = response.json()
    # 打印调试信息，比如url，data， headers等
    logging.debug(
        f"请求url: {response.request.url}\n "
        f"数据: {response.request.body}\n 返回数据: {response.text}\n ")

    if body['code'] != 0:
        logging.error("请求url: %s 出错⚠️\n 数据: %s\n 错误信息: %s", url, data, body.get('data'))
        return None

    return body.get('data', True)


def get_json_payload(data):
    """
    获取JSON格式的有效载荷。

    :param data: 需要添加到有效载荷的数据。
    :type data: dict
    :return: JSON格式的有效载荷，如果在尝试三次后`security_key`仍为空，则返回None。
    :rtype: str, None
    """
    payload = copy.deepcopy(config.get_payload())
    payload['d'] = {**data}

    if 'username' not in data and 'password' not in data:
        user = config.get('user')
        if not user:
            logging.error("用户信息为空")
            return None

        if not user.get('security_key') or not user.get('uid'):
            logging.info("security_key为空 / uid为空，尝试获取")
            user['security_key'], user['uid'] = get_user_login(user)

        payload['d'].update({'security_key': user['security_key']})

    return json.dumps(payload)
