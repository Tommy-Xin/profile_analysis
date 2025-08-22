import pandas as pd
import os
import re   
from datetime import datetime

class CollectionScorer:
    def __init__(self, df: pd.DataFrame, file_type: str):
        self.df = df.copy()
        self.file_type = file_type

        # 加载身份证地区码表
        self.id_map = {}
        id_file = os.path.join(os.path.dirname(__file__), "id_card.csv")
        if os.path.exists(id_file):
            self.id_map = pd.read_csv(id_file, dtype=str).set_index("number")["name"].to_dict()

    def parse_region_from_id(self, id_number: str):
        """根据身份证号提取地区"""
        if not isinstance(id_number, str) or len(id_number) < 6:
            return None
        code = id_number[:6]
        return self.id_map.get(code, None)

    def run_scoring(self):
        """总评分逻辑"""
        self.df["评分"] = 0

        if self.file_type == "在案":
            self._score_in_case()
        elif self.file_type == "前催":
            self._score_pre_collection()

        # 按评分排序
        self.df = self.df.sort_values("评分", ascending=False).reset_index(drop=True)
        return self.df

    def _score_in_case(self):

        """在案客户评分逻辑"""
        if "证件号" in self.df.columns:
            self.df["身份证地区"] = self.df["证件号"].apply(self.parse_region_from_id)

            if "账单地址" in self.df.columns:
                def check_region_consistency(row):
                    id_region = row["身份证地区"]
                    if id_region is None:
                        return False
                    addr = str(row["账单地址"]) if pd.notnull(row["账单地址"]) else ""
                    if addr.strip() == "":
                        return False
                    return id_region in addr

                self.df["地区一致性"] = self.df.apply(check_region_consistency, axis=1)
            else:
                # 如果没有账单地址这一列，则统一认为 False
                self.df["地区一致性"] = False

            # 加分逻辑
            self.df.loc[self.df["地区一致性"], "评分"] += 10



        #计算欠款比例
        if "本金" in self.df.columns and "当期账单金额" in self.df.columns:
            # 计算欠款/本金占比
            self.df["欠款占比"] = (self.df["当期账单金额"] / self.df["本金"]) - 1

            # 初始化分数
            self.df["欠款占比得分"] = 0

            # 区间赋分
            self.df.loc[self.df["欠款占比"] <= 0.5, "欠款占比得分"] = 10
            self.df.loc[(self.df["欠款占比"] > 0.5) & (self.df["欠款占比"] <= 1.0), "欠款占比得分"] = 8
            self.df.loc[(self.df["欠款占比"] > 1.0) & (self.df["欠款占比"] <= 1.5), "欠款占比得分"] = 5
            self.df.loc[self.df["欠款占比"] > 1.5, "欠款占比得分"] = 0

            # 加到总评分
            self.df["评分"] += self.df["欠款占比得分"]


        if "证件号" in self.df.columns:
        # 根据身份证前四位给地区评分
            def score_city_from_id(id_number):
                CITY_SCORE_MAP = {
                    # 一线城市（10分）
                    "1101": 10, "3101": 10, "4401": 10, "4403": 10,
                    # 二线城市（8分）
                    "2101": 8, "3501": 8, "2102": 8, "5301": 8, "2301": 8, "3701": 8, "4406": 8, "2201": 8,
                    "3303": 8, "1301": 8, "4501": 8, "3204": 8, "3505": 8, "3601": 8, "5201": 8, "1401": 8,
                    "3706": 8, "3304": 8, "3206": 8, "3307": 8, "4404": 8, "4413": 8, "3203": 8, "4601": 8,
                    "6501": 8, "3306": 8, "4420": 8, "3310": 8, "6201": 8, "3707": 8, "5101": 8, "3301": 8,
                    "3201": 8, "4201": 8, "3205": 8, "5001": 8, "1201": 8, "4301": 8, "3702": 8, "3302": 8,
                    "3202": 8, "6101": 8, "4101": 8, "3401": 8, "3502": 8, "4419": 8,
                    # 三线 + 四线城市（统一 5分）
                    "1306": 5, "3211": 5, "3210": 5, "4503": 5, "1302": 5, "4602": 5, "3305": 5, "1501": 5,
                    "1310": 5, "4103": 5, "3710": 5, "3209": 5, "3713": 5, "4407": 5, "4405": 5, "3212": 5,
                    "3506": 5, "1304": 5, "3708": 5, "3402": 5, "3703": 5, "6401": 5, "4502": 5, "5107": 5,
                    "4408": 5, "2103": 5, "3607": 5, "2306": 5, "4205": 5, "1502": 5, "6104": 5, "1303": 5,
                    "4302": 5, "3503": 5, "2202": 5, "3208": 5, "4412": 5, "3509": 5, "4304": 5, "3507": 5,
                    "3207": 5, "2106": 5, "5307": 5, "4452": 5, "2224": 5, "3309": 5, "3604": 5, "3508": 5,
                    "1309": 5, "2104": 5, "4206": 5, "3611": 5, "2108": 5, "3504": 5, "3403": 5, "3311": 5,
                    "4306": 5, "4418": 5, "4210": 5, "3709": 5, "3308": 5, "2111": 5, "3705": 5, "4113": 5,
                    "3405": 5, "5113": 5, "6301": 5, "4209": 5, "2302": 5, "5115": 5, "5111": 5, "4303": 5,
                    "5203": 5, "3213": 5, "4107": 5, "4115": 5, "3411": 5, "2107": 5, "4451": 5, "4211": 5,
                    "4102": 5, "5106": 5, "3714": 5, "4414": 5, "1506": 5, "1305": 5, "4409": 5, "5329": 5,
                    "4402": 5, "4114": 5, "3408": 5, "4202": 5, "3415": 5, "4509": 5, "3609": 5, "4505": 5,
                    "2310": 5, "1307": 5, "4504": 5, "3711": 5, "4212": 5, "4307": 5, "2308": 5, "5325": 5,
                    "5226": 5, "4417": 5, "1407": 5, "6105": 5, "1507": 5, "4228": 5, "4416": 5, "4310": 5,
                    "3412": 5, "3715": 5, "1402": 5, "6103": 5, "4110": 5, "1504": 5, "1408": 5, "4105": 5,
                    "1410": 5, "3418": 5, "5303": 5, "5328": 5, "4305": 5, "2114": 5, "4104": 5, "2110": 5,
                    "3717": 5, "2105": 5, "4117": 5, "4415": 5, "4108": 5, "3410": 5, "4312": 5, "2203": 5,
                    "6108": 5, "4203": 5, "3716": 5, "3610": 5, "3404": 5, "4116": 5, "5227": 5, "5105": 5,
                    "5304": 5, "5114": 5, "2205": 5, "3413": 5, "3704": 5, "5110": 5, "5109": 5, "3608": 5,
                    "1505": 5, "3602": 5, "2109": 5, "5118": 5, "2112": 5, "1308": 5, "4313": 5
                }

                if not id_number or len(id_number) < 4:
                    return 5  # 默认三四线
                code = id_number[:4]
                return CITY_SCORE_MAP.get(code, 5)

                # 初始化地区得分列
                self.df["地区得分"] = self.df["证件号"].apply(score_city_from_id)

                # 累加到总评分
                self.df["评分"] += self.df["地区得分"]


    # --------------------
        # 2. 逾期期数处理
        if "逾期期数" in self.df.columns:
            def parse_overdue(x):
                if pd.isna(x):
                    return 0
                match = re.search(r"M(\d+)", str(x).upper())
                if match:
                    return int(match.group(1))
                return 0

            self.df["逾期期数数值"] = self.df["逾期期数"].apply(parse_overdue)

            def overdue_score(m):
                if m == 0:
                    return 10
                elif 1 <= m <= 3:
                    return 10
                elif 4 <= m <= 12:
                    return 8
                elif 13 <= m <= 24:
                    return 5
                else:
                    return 0

            self.df["逾期得分"] = self.df["逾期期数数值"].apply(overdue_score)
            self.df["评分"] = self.df.get("评分", 0) + self.df["逾期得分"]


        # 年龄得分
        if "证件号" in self.df.columns:
            # 提取出生年份（身份证第 7-10 位），计算年龄
            self.df["年龄"] = pd.to_numeric(self.df["证件号"].str[6:10], errors="coerce")
            current_year = datetime.now().year
            self.df["年龄"] = self.df["年龄"].apply(lambda x: current_year - x if pd.notnull(x) else None)

            # 初始化分数列（避免 NaN）
            self.df["年龄得分"] = 0

            # 按区间赋分
            self.df.loc[self.df["年龄"].between(18, 30, inclusive="both"), "年龄得分"] = 8
            self.df.loc[self.df["年龄"].between(30, 40, inclusive="left"), "年龄得分"] = 10
            self.df.loc[self.df["年龄"].between(40, 55, inclusive="left"), "年龄得分"] = 5
            self.df.loc[self.df["年龄"] > 55, "年龄得分"] = 0

            # 加到总评分
            self.df["评分"] += self.df["年龄得分"]


        # 父母信息（联系人关系包含“父母”）
        contact_cols = [c for c in self.df.columns if "关系" in c]
        if contact_cols:
            self.df["是否有父母联系人"] = self.df[contact_cols].apply(lambda row: any("父" in str(v) for v in row), axis=1)
            self.df.loc[self.df["是否有父母联系人"], "评分"] += 5

        # 最近取现行为
        if "最后取现日期" in self.df.columns:
            self.df.loc[self.df["最后取现日期"].notnull(), "评分"] += 5

    def _score_pre_collection(self):
        """前催客户评分逻辑"""
        # 欠款金额（越大优先级越高）
        if "最新欠款" in self.df.columns:
            self.df["最新欠款"] = pd.to_numeric(self.df["最新欠款"], errors="coerce")
            self.df["评分"] += (self.df["最新欠款"] / 1000).clip(0, 20)

        # 逾期天数（适中最好，过短或过长都不佳）
        if "过期天数" in self.df.columns:
            days = pd.to_numeric(self.df["过期天数"], errors="coerce")
            self.df.loc[days.between(30, 90), "评分"] += 10

        # 是否留案
        if "留案" in self.df.columns:
            self.df.loc[self.df["留案"] == "是", "评分"] += 5
