import streamlit as st
import pandas as pd
from utils.file_loader import load_file
from utils.scoring import CollectionScorer
from utils.analyzer import CollectionAnalyzer
from utils.font_config import set_chinese_font
from utils.qwen_helper import analyze_with_qwen

set_chinese_font()

# -------------------- Streamlit 页面 --------------------
st.set_page_config(page_title="催收分析系统", layout="wide")

st.title("📊 催收用户画像分析系统（网页版）")

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

        st.subheader("🏆 评分结果（Top 20 候选人）")
        st.dataframe(scored_df.head(20))

        # 分析图表
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
            if fig: st.pyplot(fig)
            else: st.info("暂无还款数据")

        elif menu == "风险等级与还款模式":
            fig = analyzer.analyze_risk_factors()
            if fig: st.pyplot(fig)
            else: st.info("暂无风险数据")

        elif menu == "总体欠款构成":
            fig = analyzer.analyze_debt_composition()
            if fig: st.pyplot(fig)
            else: st.info("暂无欠款构成数据")

        elif menu == "欠款金额与本金占比":
            fig = analyzer.analyze_debt_ratio()
            if fig: st.pyplot(fig)
            else: st.info("暂无欠款比例数据")

        elif menu == "客户年龄分布":
            fig = analyzer.analyze_age_distribution()
            if fig: st.pyplot(fig)
            else: st.info("暂无年龄数据")

        elif menu == "客户地区分布":
            fig = analyzer.analyze_region_distribution()
            if fig: st.pyplot(fig)
            else: st.info("暂无地区数据")

        elif menu == "风险概率分布":
            fig = analyzer.analyze_risk_distribution()
            if fig: st.pyplot(fig)
            else: st.info("暂无风险概率数据")

        # ========== Qwen画像分析 ==========
        if "qwen_api_key" in st.session_state and st.button("🔍 分析TOP20并生成话术指导"):
            # profiles = "\n".join([
            #     f"客户编号: {row.get('客户编号', '未知')}, 地区: {row.get('地区', '未知')}, "
            #     f"风险等级: {row.get('风险等级', '未知')}, 还款模式: {row.get('还款模式', '未知')}, "
            #     f"欠款金额: {row.get('当期账单金额', '未知')}, 本金: {row.get('本金', '未知')}"
            #     for _, row in scored_df.head(20).iterrows()
            # ])
            profiles = scored_df.head(20)
            result = analyze_with_qwen(
                profiles,
                st.session_state["qwen_api_key"],
                st.session_state["qwen_model"]
            )
            st.subheader("💡 Qwen画像分析与话术建议")
            st.write(result)

else:
    st.info("👆 请上传文件以开始分析")



