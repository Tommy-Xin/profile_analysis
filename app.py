# app.py using the command streamlit run app.py to run
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform
import os

# -------------------- 中文字体跨平台设置 --------------------
def set_chinese_font():
    system = platform.system()

    # 常见系统字体路径
    font_paths = []
    if system == "Windows":
        font_paths = [
            r"C:\Windows\\Fonts\\msyh.ttc",      # 微软雅黑
            r"C:\Windows\\Fonts\simhei.ttf",    # 黑体
        ]
    elif system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",  
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
        ]

    # 找到可用字体
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break

    # 如果没找到，尝试用项目自带字体（放在 fonts/msyh.ttc）
    if font_path is None:
        local_font = os.path.join(os.path.dirname(__file__), "fonts", "msyh.ttc")
        if os.path.exists(local_font):
            font_path = local_font

    # 应用字体
    if font_path and os.path.exists(font_path):
        my_font = font_manager.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = my_font.get_name()
    else:
        print("⚠️ 警告：未找到中文字体，可能无法显示中文")

    plt.rcParams["axes.unicode_minus"] = False  # 负号正常显示

set_chinese_font()

# -------------------- 数据分析类 --------------------
class ThreeHandCollectionAnalyzer:
    def __init__(self, df):
        self.data = df
        self.analysis_results = {}
        self.payment_history_cols = [f'上{i}个月最小还款额' for i in range(1, 9)] + ['当期最小还款额']

    def analyze_payment_history(self):
        self.data['连续未达标月数'] = 0
        for idx, row in self.data.iterrows():
            consecutive = 0
            for col in self.payment_history_cols:
                if col in self.data.columns:
                    if pd.isna(row[col]) or row[col] <= 0:
                        consecutive += 1
                    else:
                        consecutive = 0
            self.data.at[idx, '连续未达标月数'] = consecutive

        def classify_payment_pattern(row):
            if row['连续未达标月数'] >= 6:
                return '长期拖欠'
            elif row['连续未达标月数'] >= 3:
                return '中期拖欠'
            elif row['连续未达标月数'] > 0:
                return '短期拖欠'
            else:
                return '正常还款'

        self.data['还款模式'] = self.data.apply(classify_payment_pattern, axis=1)
        self.analysis_results['还款模式分布'] = self.data['还款模式'].value_counts(normalize=True) * 100

    def analyze_risk_factors(self):
        if 'risk_prob' in self.data.columns:
            self.data['风险等级'] = pd.cut(
                self.data['risk_prob'],
                bins=[-0.01, 0.3, 0.7, 1.01],
                labels=['低风险', '中风险', '高风险']
            )
            self.analysis_results['风险等级分布'] = self.data['风险等级'].value_counts()

    def analyze_debt_composition(self):
        debt_components = [
            '本金', '应收利息', '应收费用', '违约金', '滞纳金',
            '取现手续费', '现金分期手续费', '账单分期手续费', '年费'
        ]
        debt_components = [col for col in debt_components if col in self.data.columns]
        if debt_components:
            total = self.data[debt_components].sum()
            self.analysis_results['总体欠款构成(占比)'] = total / total.sum() * 100


# -------------------- Streamlit 页面 --------------------
st.set_page_config(page_title="三手催收分析系统", layout="wide")

st.title("📊 催收用户画像分析系统（网页版）")

uploaded_file = st.file_uploader("请上传 2406 三手 Excel 文件", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    analyzer = ThreeHandCollectionAnalyzer(df)
    analyzer.analyze_payment_history()
    analyzer.analyze_risk_factors()
    analyzer.analyze_debt_composition()

    # 左侧菜单
    menu = st.sidebar.radio("选择分析视图", [
        "还款模式分布",
        "风险等级与还款模式",
        "总体欠款构成"
    ])

    if menu == "还款模式分布":
        if '还款模式分布' in analyzer.analysis_results:
            data = analyzer.analysis_results['还款模式分布'].sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(x=data.index, y=data.values, ax=ax)
            for i, v in enumerate(data.values):
                ax.text(i, v + 0.5, f'{v:.1f}%', ha='center')
            ax.set_title("还款模式分布（%）")
            st.pyplot(fig)

    elif menu == "风险等级与还款模式":
        if '风险等级' in df.columns and '还款模式' in df.columns:
            cross = pd.crosstab(df['风险等级'], df['还款模式'], normalize='index') * 100
            fig, ax = plt.subplots(figsize=(8, 5))
            cross.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
            ax.set_ylabel("占比（%）")
            ax.set_title("不同风险等级的还款模式占比")
            st.pyplot(fig)

    elif menu == "总体欠款构成":
        if '总体欠款构成(占比)' in analyzer.analysis_results:
            data = analyzer.analysis_results['总体欠款构成(占比)'].sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(data, labels=data.index, autopct='%1.1f%%', startangle=90)
            ax.set_title("总体欠款构成占比")
            st.pyplot(fig)

else:
    st.info("请先上传数据文件进行分析")