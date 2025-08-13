from nonebot import get_plugin_config
import nonebot
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.message import event_preprocessor
from nonebot import get_driver
import httpx
import jwt
from datetime import datetime, timedelta
import time
from .config import Config
import base64
import random
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="卖若插件",
    description="基于 LLM 的卖若插件",
    usage="none",
    type="application",
    homepage="https://github.com/XTxiaoting14332/nonebot-plugin-sell-poor",
    config=Config,
    supported_adapters={"~onebot.v11"},

)

_config = get_plugin_config(Config)
driver = get_driver()

def generate_token(apikey: str):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("错误的apikey！", e)

    payload = {
        "api_key": id,
        "exp": datetime.utcnow() + timedelta(days=1),
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


token = _config.sell_poor_token
text = _config.sell_poor_text

if token.strip() == "":
    logger.error("未配置token，请在配置文件中设置 sell_poor_token")


@event_preprocessor
async def handle(bot: Bot, event: GroupMessageEvent):
    Bot = nonebot.get_bot()
    for i in event.message:
        if i.type == "text":
            msg = i.data["text"]
            if random.random() < _config.sell_poor_probability and str(event.group_id) in _config.sell_poor_group:
                auth = generate_token(token)
                res = await req_glm(auth, str(msg).strip())
                try:
                    if is_error_response(res):
                        await Bot.finish()
                        return
                except ValueError:
                    await Bot.finish()
                    return

                reply_map = {
                    "sell_poor_y": text
                }
                if res not in reply_map:
                    return
                reply_message = reply_map.get(res)
                await Bot.send_group_msg(group_id=event.group_id, message=reply_message)

# 异步请求AI
# 异步请求AI
async def req_glm(auth_token, msg):
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    
    prompt = (
        "需要你进行以下判断，并仅回复符合的标签："
        "1.以下这段文字是否出现了技术性的内容（比如计算机领域，游戏领域等各方面，生活日常不算），如果出现了，请仅回复'sell_poor_y'"
        "2.如果不符合请回复'none'"
        "需要判断的文字是："
    )
    
    data = {
        "model": "glm-4-flash",
        "temperature": 0.3,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt + msg 
                }
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=20, write=20, pool=30)) as client:
        res = await client.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, json=data)
        res = res.json()
    try:
        res_raw = res['choices'][0]['message']['content']
        # logger.info(f"模型返回: {res_raw}")
    except Exception as e:
        res_raw = res
    return res_raw




# 检查返回是否为错误
def is_error_response(res):
    if isinstance(res, dict) and 'error' in res:
        error_code = res['error'].get('code')
        # 处理错误代码 1301（敏感内容）
        if error_code == '1301':
            # logger.info(f"模型敏感内容: {res['error']['message']}")
            return True
        # 处理错误代码 1210（不支持的图片）
        elif error_code == '1210':
            # logger.info("接收到不支持的图片")
            raise ValueError("不支持的图片")  # 抛出异常来阻止后续逻辑
    return False