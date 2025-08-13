from pydantic import BaseModel

class Config(BaseModel):

    # 用户token
    sell_poor_token: str = ""

    # 触发概率
    sell_poor_probability: float = 0.5

    # 启用的群号
    sell_poor_group: list = []

    # 卖若文案
    sell_poor_text: str = "诶，还是太菜了，学不来，我也想有本领😭"