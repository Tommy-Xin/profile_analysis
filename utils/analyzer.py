import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class CollectionAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.data = df
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

    def analyze_debt_composition(self):
        """总体欠款构成"""
        debt_components = [
            '本金', '应收利息', '应收费用', '违约金', '滞纳金',
            '取现手续费', '现金分期手续费', '账单分期手续费', '年费'
        ]
        debt_components = [col for col in debt_components if col in self.data.columns]
        if not debt_components:
            return None

        total = self.data[debt_components].sum()
        self.analysis_results['总体欠款构成(占比)'] = total / total.sum() * 100

        fig, ax = plt.subplots(figsize=(6, 6))
        data = self.analysis_results['总体欠款构成(占比)'].sort_values(ascending=False)
        ax.pie(data, labels=data.index, autopct='%1.1f%%', startangle=90)
        ax.set_title("总体欠款构成占比")
        return fig

    def analyze_debt_ratio(self):
        """欠款金额与本金占比分布"""
        if "欠款金额" not in self.data.columns or "本金" not in self.data.columns:
            return None
        
        self.data["欠款比例"] = self.data["欠款金额"] / self.data["本金"].replace(0, pd.NA)
        
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

    def analyze_region_distribution(self):
        """客户地区分布（省份/城市）"""
        if "地区" not in self.data.columns:
            return None
        
        dist = self.data["地区"].value_counts().head(10)  # 只看 Top10
        self.analysis_results["地区分布"] = dist
        
        fig, ax = plt.subplots(figsize=(8,5))
        sns.barplot(y=dist.index, x=dist.values, ax=ax)
        for i, v in enumerate(dist.values):
            ax.text(v + 0.5, i, f"{v}", va="center")
        ax.set_title("客户地区分布（Top 10）")
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
