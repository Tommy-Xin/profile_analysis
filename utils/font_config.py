import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform, os
plt.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]
#plt.rcParams["font.family"] = ["Arial Unicode MS", "Helvetica", "Arial", "sans-serif"]
def set_chinese_font():
    system = platform.system()
    font_paths = []
    if system == "Windows":
        font_paths = [r"C:\Windows\\Fonts\\msyh.ttc", r"C:\Windows\\Fonts\simhei.ttf"]
    elif system == "Darwin":  # macOS
        font_paths = ["/System/Library/Fonts/STHeiti Light.ttc"]
    else:  # Linux
        font_paths = ["STHeiti Light.ttc"]

    font_path = None
    # 获取 STHeiti Light.ttf 的字体名称
    font_path = "STHeiti Light.ttc"
    font_name = font_manager.FontProperties(fname=font_path).get_name()

    # 设置为全局默认字体
    plt.rcParams["font.family"] = font_name
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    if font_path:
        my_font = font_manager.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = my_font.get_name()

    plt.rcParams["axes.unicode_minus"] = False
