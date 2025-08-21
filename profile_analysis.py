import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
sns.set(font="SimHei", font_scale=1.2)
plt.rcParams['axes.unicode_minus'] = False


class ThreeHandCollectionAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        self.analysis_results = {}
        
    def load_data(self):
        """加载并预处理2406三手数据"""
        try:
            self.data = pd.read_excel(self.file_path)
            print(f"成功加载数据：{self.data.shape[0]}条记录，{self.data.shape[1]}列")
            
            # 处理日期列
            date_columns = [col for col in self.data.columns if '日期' in col]
            for col in date_columns:
                self.data[col] = pd.to_datetime(self.data[col], errors='coerce')
            
            # 处理金额列
            money_columns = [col for col in self.data.columns 
                           if '金额' in col or '款' in col or '费' in col or '息' in col]
            for col in money_columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                
            # 历史还款列
            self.payment_history_cols = [f'上{i}个月最小还款额' for i in range(1,9)] + ['当期最小还款额']
            
            return self.data
        except Exception as e:
            print(f"数据加载失败: {str(e)}")
            return None
    
    def analyze_payment_history(self):
        """分析历史还款模式"""
        if self.data is None:
            print("请先加载数据")
            return
        
        payment_analysis = {}
        
        # 连续未达标月数
        self.data['连续未达标月数'] = 0
        for idx, row in self.data.iterrows():
            consecutive = 0
            for col in self.payment_history_cols:
                if pd.isna(row[col]) or row[col] <= 0:
                    consecutive += 1
                else:
                    consecutive = 0
            self.data.at[idx, '连续未达标月数'] = consecutive
        
        # 分类
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
        payment_analysis['还款模式分布'] = self.data['还款模式'].value_counts(normalize=True) * 100
        
        # 历史还款与总欠款相关性
        if '总欠款' in self.data.columns:
            corr_data = self.data[[col for col in self.payment_history_cols if col in self.data.columns] + ['总欠款']]
            payment_analysis['历史还款与总欠款相关性'] = corr_data.corr()['总欠款']
        
        self.analysis_results['payment_history'] = payment_analysis
        print("历史还款模式分析完成")
        return payment_analysis
    
    def analyze_risk_factors(self):
        """分析风险因素"""
        if self.data is None:
            print("请先加载数据")
            return
        
        risk_analysis = {}
        
        if 'risk_prob' in self.data.columns:
            risk_analysis['risk_prob分布'] = self.data['risk_prob'].describe()
            self.data['风险等级'] = pd.cut(
                self.data['risk_prob'],
                bins=[-0.01, 0.3, 0.7, 1.01],
                labels=['低风险', '中风险', '高风险']
            )
            risk_analysis['风险等级分布'] = self.data['风险等级'].value_counts()
        
        if '逾期天数' in self.data.columns and 'risk_prob' in self.data.columns:
            risk_analysis['逾期天数与风险相关性'] = self.data['逾期天数'].corr(self.data['risk_prob'])
        
        if '近两年内逾期次数' in self.data.columns:
            risk_analysis['近两年内逾期次数分布'] = self.data['近两年内逾期次数'].value_counts()
            if '总欠款' in self.data.columns:
                risk_analysis['逾期次数与总欠款关系'] = self.data.groupby('近两年内逾期次数')['总欠款'].mean()
        
        self.analysis_results['risk_factors'] = risk_analysis
        print("风险因素分析完成")
        return risk_analysis
    
    def analyze_debt_composition(self):
        """分析欠款构成"""
        if self.data is None:
            print("请先加载数据")
            return
        
        debt_components = [
            '本金', '应收利息', '应收费用', '违约金', '滞纳金',
            '取现手续费', '现金分期手续费', '账单分期手续费', '年费'
        ]
        debt_components = [col for col in debt_components if col in self.data.columns]
        
        if not debt_components:
            print("未找到欠款构成相关列")
            return
        
        debt_analysis = {}
        debt_analysis['总体欠款构成(总额)'] = self.data[debt_components].sum()
        debt_analysis['总体欠款构成(占比)'] = (
            debt_analysis['总体欠款构成(总额)'] /
            debt_analysis['总体欠款构成(总额)'].sum() * 100
        )
        
        if '逾期天数' in self.data.columns:
            self.data['逾期天数分组'] = pd.cut(
                self.data['逾期天数'],
                bins=[-1, 30, 90, 180, 360, float('inf')],
                labels=['30天内', '31-90天', '91-180天', '181-360天', '360天以上']
            )
            debt_analysis['按逾期天数分组的欠款构成'] = self.data.groupby('逾期天数分组')[debt_components].sum()
        
        self.analysis_results['debt_composition'] = debt_analysis
        print("欠款构成分析完成")
        return debt_analysis


class ThreeHandCollectionAnalyzerInteractive(ThreeHandCollectionAnalyzer):
    def visualize_menu(self):
        """动态菜单可视化"""
        if not self.analysis_results:
            print("请先执行数据分析")
            return
        
        menu = {
            "1": "还款模式分布",
            "2": "风险等级与还款模式关系",
            "3": "欠款构成饼图",
            "4": "逾期天数与风险概率关系",
            "5": "历史逾期次数与总欠款关系",
            "q": "退出"
        }
        
        while True:
            print("\n=== 可视化菜单 ===")
            for k, v in menu.items():
                print(f"{k}. {v}")
            
            choice = input("请选择要查看的图表编号（q退出）：").strip()
            if choice.lower() == 'q':
                print("退出可视化菜单")
                break
            
            if choice not in menu:
                print("无效选择，请重新输入")
                continue
            
            if choice == "1":
                payment_patterns = self.analysis_results['payment_history']['还款模式分布'].sort_values(ascending=False)
                plt.figure(figsize=(10, 6))
                ax = sns.barplot(x=payment_patterns.index, y=payment_patterns.values)
                plt.title('历史还款模式分布(%)', fontsize=16)
                for i, v in enumerate(payment_patterns.values):
                    ax.text(i, v + 0.5, f'{v:.1f}%', ha='center')
                plt.show()
            
            elif choice == "2":
                if 'risk_prob' in self.data.columns and '还款模式' in self.data.columns:
                    risk_payment = pd.crosstab(self.data['风险等级'], self.data['还款模式'], normalize='index') * 100
                    risk_payment = risk_payment.loc[:, risk_payment.mean().sort_values(ascending=False).index]
                    risk_payment.plot(kind='bar', stacked=True, colormap='viridis', figsize=(12, 7))
                    plt.title('不同风险等级的还款模式分布(%)', fontsize=16)
                    plt.ylabel('占比(%)')
                    plt.xlabel('风险等级')
                    plt.xticks(rotation=0)
                    plt.show()
            
            elif choice == "3":
                debt_composition = self.analysis_results['debt_composition']['总体欠款构成(占比)'].sort_values(ascending=False)
                plt.figure(figsize=(10, 10))
                plt.pie(debt_composition, labels=debt_composition.index, autopct='%1.1f%%',
                        startangle=90, colors=sns.color_palette('pastel'))
                plt.title('总体欠款构成占比', fontsize=16)
                plt.show()
            
            elif choice == "4":
                plt.figure(figsize=(12, 7))
                sns.scatterplot(x='逾期天数', y='risk_prob', hue='风险等级', data=self.data,
                                alpha=0.6, s=100)
                plt.title('逾期天数与风险概率关系', fontsize=16)
                plt.show()
            
            elif choice == "5":
                if 'risk_factors' in self.analysis_results and '逾期次数与总欠款关系' in self.analysis_results['risk_factors']:
                    rel = self.analysis_results['risk_factors']['逾期次数与总欠款关系'].sort_values(ascending=False)
                    plt.figure(figsize=(12, 7))
                    ax = sns.barplot(x=rel.index, y=rel.values)
                    plt.title('历史逾期次数与平均总欠款关系', fontsize=16)
                    for i, v in enumerate(rel.values):
                        ax.text(i, v + 100, f'{v:.0f}', ha='center')
                    plt.show()


def main():
    root_dir = r'D:\project\collection\data\qd'
    file_path = os.path.join(root_dir, "2406三手.xlsx")
    
    analyzer = ThreeHandCollectionAnalyzerInteractive(file_path)
    analyzer.load_data()
    analyzer.analyze_payment_history()
    analyzer.analyze_risk_factors()
    analyzer.analyze_debt_composition()
    
    analyzer.visualize_menu()


if __name__ == "__main__":
    main()
