# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from utils.file_loader import load_file
from utils.scoring import CollectionScorer
from utils.analyzer import CollectionAnalyzer
from utils.font_config import set_chinese_font
from utils.qwen_helper import analyze_with_qwen


set_chinese_font()

st.set_page_config(page_title="催收分析系统", layout="wide")
st.title("📊 催收用户画像分析系统")

st.markdown("""
欢迎使用 **催收用户画像分析系统** 🎉  

👉 使用流程：
1. 上传 Excel 文件（在案 / 前催）
2. 选择分析类型：  
   - **基础数据统计**  
   - **最容易还款人员画像与话术指导**
""")

# ========== API Key & 模型选择 ==========
api_key = st.sidebar.text_input("请输入 Qwen API Key：", type="password")
model_choice = st.sidebar.selectbox(
    "选择调用模型：",
    ["qwen-turbo", "qwen-plus", "qwen-max"],
    index=1
)

if api_key:
    st.session_state["qwen_api_key"] = api_key
    st.session_state["qwen_model"] = model_choice
    st.sidebar.success(f"✅ 已保存 API Key，使用模型：{model_choice}")
else:
    st.sidebar.warning("⚠️ 请输入 Qwen API Key 才能使用画像分析功能")

# 上传文件
uploaded_file = st.file_uploader("请上传 Excel 文件（在案 / 前催）", type=["xlsx"])
if uploaded_file:
    df, file_type = load_file(uploaded_file)

    if df is None:
        st.error("❌ 文件读取失败，请检查格式")
    else:
        st.success(f"✅ 文件加载成功，识别为 **{file_type}**")

        # 打分
        scorer = CollectionScorer(df, file_type)
        scored_df = scorer.run_scoring()

        # 用户选择分析类型
        analysis_mode = st.radio(
            "请选择分析方向：",
            ["📈 基础数据统计", "💡 最容易还款人员画像与话术"]
        )

        if analysis_mode == "📈 基础数据统计":
            analyzer = CollectionAnalyzer(scored_df)
            menu = st.sidebar.radio("选择分析视图", [
                "还款模式分布",
                "风险等级与还款模式",
                "总体欠款构成",
                "欠款金额与本金占比",
                "客户年龄分布",
                "客户地区分布",
                "风险概率分布"
            ])

            if menu == "还款模式分布":
                fig = analyzer.analyze_payment_history()
                if fig:
                    st.pyplot(fig)
                else:
                    st.info('暂无还款数据')

            elif menu == "风险等级与还款模式":
                fig = analyzer.analyze_risk_factors()
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("暂无风险数据")

            elif menu == "总体欠款构成":
                fig = analyzer.analyze_debt_composition()
                if fig:
                    st.pyplot(fig)
                else:
                    st.info('暂无欠款构成数据')

            elif menu == "欠款金额与本金占比":
                fig = analyzer.analyze_debt_ratio()
                if fig:
                    st.pyplot(fig)
                else:
                    st.info('暂无欠款比例数据')

            elif menu == "客户年龄分布":
                fig = analyzer.analyze_age_distribution()
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("暂无年龄数据")

            elif menu == "客户地区分布":
                top_n = st.number_input("请选择要显示的前 N 个地区", min_value=5, max_value=50, value=10, step=1)
                fig = analyzer.analyze_region_distribution(top_n=top_n)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("暂无地区数据")

            elif menu == "风险概率分布":
                fig = analyzer.analyze_risk_distribution()
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("暂无风险概率数据")

        elif analysis_mode == "💡 最容易还款人员画像与话术":
            k = st.slider("选择要分析的候选人数", min_value=5, max_value=100, value=20, step=5)
            selected_df = scored_df.head(k)
            st.subheader(f"🏆 候选人 Top {k}")
            st.dataframe(selected_df)

            if "qwen_api_key" in st.session_state and st.button("🔍 生成话术指导"):
                result = analyze_with_qwen(
                    selected_df,
                    st.session_state["qwen_api_key"],
                    st.session_state["qwen_model"]
                )
                st.subheader("💡 Qwen画像分析与话术建议")
                st.write(result)



