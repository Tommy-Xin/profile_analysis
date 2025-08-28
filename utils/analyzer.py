import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from adjustText import adjust_text  
#plt.rcParams["font.family"] = ["Arial Unicode MS", "Helvetica", "Arial", "sans-serif"]
class CollectionAnalyzer:
    def __init__(self, df: pd.DataFrame, file_type: str = None):
        self.data = df
        # self.file_type = file_type
        self.analysis_results = {}
        self.payment_history_cols = [
            "上个月最小还款额",
            "上2个月最小还款额",
            "上3个月最小还款额",
            "上4个月最小还款额",
            "上5个月最小还款额",
            "上6个月最小还款额",
            "上7个月最小还款额",
            "上8个月最小还款额",
            "当期最小还款额"
        ]

    def analyze_payment_history(self):
        """分析还款模式"""
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

        fig, ax = plt.subplots(figsize=(8, 5))
        data = self.analysis_results['还款模式分布'].sort_values(ascending=False)
        sns.barplot(x=data.index, y=data.values, ax=ax)
        for i, v in enumerate(data.values):
            ax.text(i, v + 0.5, f'{v:.1f}%', ha='center')
        ax.set_title("还款模式分布（%）")
        return fig

    def analyze_risk_factors(self):
        """风险等级与还款模式"""
        if 'risk_prob' in self.data.columns:
            self.data['风险等级'] = pd.cut(
                self.data['risk_prob'],
                bins=[-0.01, 0.3, 0.7, 1.01],
                labels=['低风险', '中风险', '高风险']
            )
        if '风险等级' not in self.data.columns or '还款模式' not in self.data.columns:
            return None

        cross = pd.crosstab(self.data['风险等级'], self.data['还款模式'], normalize='index') * 100
        self.analysis_results['风险等级分布'] = cross

        fig, ax = plt.subplots(figsize=(8, 5))
        cross.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
        ax.set_ylabel("占比（%）")
        ax.set_title("不同风险等级的还款模式占比")
        return fig

    # def analyze_debt_composition(self):
    #     """总体欠款构成"""
    #     debt_components = [
    #         '本金', '应收利息', '应收费用', '违约金', '滞纳金',
    #         '取现手续费', '现金分期手续费', '账单分期手续费', '年费'
    #     ]
    #     debt_components = [col for col in debt_components if col in self.data.columns]
    #     if not debt_components:
    #         return None

    #     total = self.data[debt_components].sum()
    #     self.analysis_results['总体欠款构成(占比)'] = total / total.sum() * 100

    #     data = self.analysis_results['总体欠款构成(占比)'].sort_values(ascending=False)
    #     fig, ax = plt.subplots(figsize=(8, 8))
        
    #     wedges, texts = ax.pie(data, startangle=90, radius=1.2, wedgeprops=dict(width=0.4, edgecolor='w'))

    #     # 添加箭头 + 标签
    #     for i, p in enumerate(wedges):
    #         ang = (p.theta2 - p.theta1)/2. + p.theta1
    #         y = np.sin(np.deg2rad(ang))
    #         x = np.cos(np.deg2rad(ang))
    #         horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
    #         connectionstyle = "angle,angleA=0,angleB={}".format(ang)
    #         ax.annotate(f"{data.index[i]}: {data.values[i]:.1f}%", 
    #                     xy=(x, y), xytext=(1.5*np.sign(x), 1.5*y),
    #                     horizontalalignment=horizontalalignment,
    #                     arrowprops=dict(arrowstyle="-", connectionstyle=connectionstyle))

    #     ax.set_title("总体欠款构成占比")
    #     return fig

    def analyze_debt_composition(self):
    
        debt_components = [
            '本金', '应收利息', '应收费用', '违约金', '滞纳金',
            '取现手续费', '现金分期手续费', '账单分期手续费', '年费'
        ]
        debt_components = [col for col in debt_components if col in self.data.columns]
        if not debt_components:
            return None

        total = self.data[debt_components].sum()
        data = (total / total.sum() * 100).sort_values(ascending=False)
        self.analysis_results['总体欠款构成(占比)'] = data

        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts= ax.pie(
            data,
            labels=None,  # 不在扇区显示文字
            autopct=None,
            startangle=90,
            radius=1.2,
            wedgeprops=dict(width=0.4, edgecolor='w')
        )

        # 添加图例，放在右上角
        ax.legend(
            wedges,
            [f"{idx}: {val:.1f}%" for idx, val in zip(data.index, data.values)],
            title="欠款构成",
            loc="upper right",
            bbox_to_anchor=(1.3, 1),
            fontsize=8
        )

        ax.set_title("总体欠款构成占比")
        return fig



    def analyze_debt_ratio(self):
        """欠款金额与本金占比分布"""
        if "本金" in self.data.columns and "当期账单金额" in self.data.columns:
            self.data["欠款比例"] = (self.data["当期账单金额"] / self.data["本金"]) - 1
        
        def classify_ratio(r):
            if pd.isna(r): return "无效数据"
            if r <= 0.5: return "50%以下"
            elif r <= 1.0: return "51%-100%"
            elif r <= 1.5: return "101%-150%"
            else: return "＞150%"
        
        self.data["欠款比例区间"] = self.data["欠款比例"].apply(classify_ratio)
        dist = self.data["欠款比例区间"].value_counts(normalize=True) * 100
        self.analysis_results["欠款比例分布"] = dist
        
        fig, ax = plt.subplots(figsize=(6,4))
        sns.barplot(x=dist.index, y=dist.values, ax=ax)
        for i, v in enumerate(dist.values):
            ax.text(i, v + 0.5, f"{v:.1f}%", ha="center")
        ax.set_title("欠款金额与本金比例分布")
        return fig

    def analyze_age_distribution(self):
        """客户年龄分布"""
        if "年龄" not in self.data.columns:
            return None
        
        bins = [0, 20, 30, 40, 50, 60, 100]
        labels = ["20以下","21-30","31-40","41-50","51-60","60以上"]
        self.data["年龄段"] = pd.cut(self.data["年龄"], bins=bins, labels=labels, right=True)
        dist = self.data["年龄段"].value_counts(normalize=True).sort_index() * 100
        self.analysis_results["年龄分布"] = dist
        
        fig, ax = plt.subplots(figsize=(7,4))
        sns.barplot(x=dist.index, y=dist.values, ax=ax)
        for i, v in enumerate(dist.values):
            ax.text(i, v + 0.5, f"{v:.1f}%", ha="center")
        ax.set_title("客户年龄结构（%）")
        return fig

    def analyze_region_distribution(self, id_file="utils/id_card.csv", top_n=10, ascending=False):
        """客户地区分布（根据身份证号前6位解析省市，用户可选择 Top N 和排序方式）"""
        if "证件号" not in self.data.columns:
            return None

        # 1. 加载地区映射表
        try:
            self.id_map = pd.read_csv(id_file, dtype=str).set_index("number")["name"].to_dict()
        except Exception as e:
            print(f"⚠️ 地区映射表加载失败: {e}")
            return None

        # 2. 定义身份证解析函数
        def parse_region_from_id(id_number: str):
            if not isinstance(id_number, str) or len(id_number) < 6:
                return None
            code = id_number[:6]
            return self.id_map.get(code, None)

        # 3. 生成地区列
        self.data["地区(解析)"] = self.data["证件号"].apply(parse_region_from_id)

        if self.data["地区(解析)"].isna().all():
            return None

        # 4. 统计地区分布
        dist = self.data["地区(解析)"].value_counts(ascending=ascending).head(top_n)
        self.analysis_results["地区分布"] = dist

        # 5. 画图
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(y=dist.index, x=dist.values, ax=ax)
        for i, v in enumerate(dist.values):
            ax.text(v + 0.5, i, f"{v}", va="center")
        ax.set_title(f"客户地区分布（Top {top_n}）")
        return fig


    def analyze_risk_distribution(self):
        """风险概率直方图"""
        if "risk_prob" not in self.data.columns:
            return None
        
        fig, ax = plt.subplots(figsize=(7,4))
        self.data["risk_prob"].hist(bins=20, ax=ax)
        ax.set_xlabel("风险概率")
        ax.set_ylabel("人数")
        ax.set_title("风险概率分布直方图")
        return fig
