from api import *
from config import Config

# 全局变量
config = Config()


def pass_function():
    pass


def process_tasks():
    fail_info = []
    success_info = []
    # 签到
    status, msg = task_complete(8)
    success_info.append(msg) if status else fail_info.append(msg)

    user_pre = get_user_liteInfo()
    # 定义任务ID到函数的映射
    task_id_to_function = {
        1: get_article_detail,
        2: add_collection,
        3: pass_function,
        5: share_article,
        6: coin_use,
    }

    # 首先获取目标文章
    target_article_id = get_target_article()

    success_count = 0
    try_time_limit = 20
    try_time = 0
    while success_count < 5:
        time.sleep(1)  # 防止请求过快
        success_count = 0
        task_list = get_tasks_list()
        tasks = task_list.get('items')

        if not tasks:
            logging.error("无法获取任务列表，程序退出")
            fail_info.append("获取任务列表失败⚠️")
            return

        for task in tasks:
            if task['status'] == 0:
                # 从映射中获取对应的函数
                if task['id'] == 3:
                    # 如果是点赞任务，直接算成功
                    success_count += 1
                    continue
                task_function = task_id_to_function.get(task['id'])
                if task_function:
                    # 执行函数
                    task_function(target_article_id)
                else:
                    logging.error(f"未找到任务ID {task['id']} 对应的函数")
            elif task['status'] == 1:
                status, msg = task_complete(task['id'])
                success_info.append(msg) if status else fail_info.append(msg)
            elif task['status'] == 2:
                success_count += 1

        try_time += 1
        if try_time > try_time_limit:
            fail_info.append("尝试次数超过限制⚠️")
            break

    # 领取总任务奖励
    task_list = get_tasks_list()
    if task_list.get('status', 0) != 0:
        status, msg = task_complete(task_list.get('id', 7))
        success_info.append(msg) if status else fail_info.append(msg)

    # 删除收藏
    del_collection(target_article_id)

    # 获取硬币、经验
    user_post = get_user_liteInfo()
    try:
        username = user_post['nickname']
        coin = user_post['coin'] - user_pre['coin']
        exp = user_post['exp'] - user_pre['exp']
    except Exception as e:
        logging.error(f"硬币、经验获取失败⚠️{e}")
        coin = 0
        exp = 0
        username = "获取失败⚠️"

    # 推送信息
    push_msg = (
            f"📅 {datetime.now().strftime('%Y-%m-%d')} "
            f"用户👤{username} 硬币💰{coin} 经验🌟{exp} \n"
            + (f"🎉成功\n" + '\n'.join(success_info) if success_info else '')
            + (f"🚫失败\n" + '\n'.join(fail_info) if fail_info else '')
    )
    config.push_message(push_msg)


def main():
    enable = config.get('enable')
    if enable is False:
        logging.info("程序已禁用")
        return

    logging.info("程序开始运行")
    try:
        process_tasks()
    except Exception as e:
        logging.error(f"主程序出现异常⚠️{e}")
    config.save()


if __name__ == "__main__":
    main()
