import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform, os

def set_chinese_font():
    system = platform.system()
    font_paths = []
    if system == "Windows":
        font_paths = [r"C:\Windows\\Fonts\\msyh.ttc", r"C:\Windows\\Fonts\simhei.ttf"]
    elif system == "Darwin":  # macOS
        font_paths = ["/System/Library/Fonts/STHeiti Light.ttc"]
    else:  # Linux
        font_paths = ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]

    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    if font_path:
        my_font = font_manager.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = my_font.get_name()

    plt.rcParams["axes.unicode_minus"] = False
