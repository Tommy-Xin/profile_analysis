# utils/qwen_helper.py
import dashscope
import pandas as pd
from http import HTTPStatus

def analyze_with_qwen(user_profiles: pd.DataFrame, api_key: str, model: str = "qwen-plus") -> str:
    """
    调用 Qwen 分析客户画像并生成逐用户催收话术。
    :param user_profiles: DataFrame (TOP N用户画像)
    :param api_key: Qwen API Key
    :param model: Qwen 模型 (默认 qwen-plus)
    """
    dashscope.api_key = api_key

    # 把前20行用户画像转成文本，带上关键字段
    profiles_text = user_profiles.to_string(index=False)

    prompt = f"""
你是一个资深的催收专家。

下面是20位客户的画像（包含评分、风险等级、还款模式、本金、账单金额、欠款比例等数据）。

请你逐个客户进行分析，并输出以下内容：

1. 用户编号或基本信息（用表格中的数据标识即可）
2. 核心风险特征总结（简要2-3句话）
3. 催收话术思路（以姓氏+先生/女生开头，比如缓和安抚型、直接强硬型、风险提醒型、情感沟通型等）
4. 示例话术（2-3条，真实可直接使用）

客户画像数据如下：
{profiles_text}

请严格按照以下格式输出：
---
【客户1】
风险特征: ...
话术思路: ...
具体话术:
- ...
- ...

【客户2】
风险特征: ...
话术思路: ...
具体话术:
- ...
- ...
---
"""

    response = dashscope.Generation.call(
        model=model,
        prompt=prompt,
        top_p=0.8,
        temperature=0.7
    )

    if response.status_code == HTTPStatus.OK:
        return response.output["text"]
    else:
        return f"❌ 调用失败: {response.code}, {response.message}"

