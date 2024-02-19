import logging
import os

import toml
from onepush import get_notifier

logging = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self):
        # 读取环境变量LK_prefix获取配置文件前缀
        prefix = os.environ.get('LK_prefix', 'LK_')
        path = os.environ.get('LK_path', '.')

        logging.info(f"读取配置文件，环境变量LK_prefix={prefix}, LK_path={path}")

        # 在路径中搜索配置文件
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.startswith(prefix) and file.endswith('.toml') and not file.endswith('.example.toml'):
                    self.file = os.path.join(root, file)
                    self.config = toml.load(self.file)
                    logging.info(f"找到配置文件{file}，路径为{root}")
                    return

        # 如果没有找到配置文件，抛出异常
        logging.error(f"找不到配置文件，环境变量LK_prefix={prefix}, LK_path={path}")
        raise FileNotFoundError(f"找不到配置文件，环境变量LK_prefix={prefix}, LK_path={path}")

    def save(self):
        # 保存配置文件
        toml.dump(self.config, open(self.file, 'w'))

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_headers(self):
        return self.config.get('headers', {})

    def get_payload(self):
        return self.config.get('payload', {})

    def push_message(self, content):
        notifier = get_notifier('wechatworkapp')
        wechat_params = self.config.get('wechat_params')

        params = {
            'agentid': wechat_params.get('agentid'),
            'corpid': wechat_params.get('corpid'),
            'corpsecret': wechat_params.get('corpsecret'),
        }

        content_params = {
            'title': "【LK】每日任务",
            'content': content
        }

        try:
            res = notifier.notify(**params, **content_params).json()
            if res['errmsg'] == 'ok':
                logging.info("推送消息成功")
            else:
                logging.error("推送消息失败，错误信息：{}".format(res['errmsg']))
        except Exception as e:
            logging.error("推送消息失败，错误信息：{}".format(e))
