import pandas as pd

def detect_file_type(filename: str) -> str:
    """根据文件名判断是 '在案' 还是 '前催'"""
    if "前催" in filename:
        return "前催"
    return "在案"

def load_file(uploaded_file):
    """
    读取 Excel，并根据文件名判断类型
    - 文件名包含 "前催" -> 前催
    - 否则 -> 在案
    """
    df = pd.read_excel(uploaded_file)

    filename = uploaded_file.name  # 获取上传文件名
    if "前催" in filename:
        file_type = "前催"
    else:
        file_type = "在案"

    return df, file_type
