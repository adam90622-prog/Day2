import streamlit as st
import pandas as pd
import altair as alt
import io

# ── 페이지 설정 ───────────────────────────────────────────────────
st.set_page_config(
    page_title="고객 통합 대시보드",
    page_icon="🏦",
    layout="wide",
)

# ── 커스텀 CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 2.5rem 3rem 2rem 3rem; max-width: 1200px; }

h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #4f46e5, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem !important;
}
h2, h3 { color: #374151 !important; font-weight: 700 !important; }

[data-testid="stMetric"] {
    background: white;
    border-radius: 16px;
    padding: 1.2rem 1.6rem;
    box-shadow: 0 2px 12px rgba(79,70,229,0.10);
    border-left: 5px solid #4f46e5;
}
[data-testid="stMetricLabel"] { font-size: 0.95rem !important; color: #6b7280 !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 800 !important; color: #1e1b4b !important; }
hr { border-color: #e5e7eb !important; margin: 1.5rem 0 !important; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)


# ── 엑셀 로드 함수 ────────────────────────────────────────────────
def load_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"파일을 읽을 수 없습니다: {e}")
        return None


# ══════════════════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════════════════
st.title("🏦 고객 통합 대시보드")
st.caption("두 개의 고객 데이터 파일을 업로드하면 고객ID 기준으로 병합하여 분석합니다.")

st.divider()

# ══════════════════════════════════════════════════════════════════
# 업로드 섹션
# ══════════════════════════════════════════════════════════════════
st.subheader("📂 엑셀 파일 업로드")

with st.expander("📋 파일 형식 안내", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**파일 1 — 고객 기본정보**

| 컬럼 | 예시 |
|------|------|
| 고객ID | C001 |
| 연령 | 42 |
| 고객등급 | VIP |
| 총자산_백만원 | 500 |
| 투자성향 | 적극투자형 |
| 가입연도 | 2019 |
""")
    with col_b:
        st.markdown("""
**파일 2 — 고객 거래정보**

| 컬럼 | 예시 |
|------|------|
| 고객ID | C001 |
| 주요가입상품 | 펀드 |
| 수익률_pct | 5.2 |
| 관리점포 | 강남점 |
| 최근3개월_거래횟수 | 7 |
| 디지털플랫폼_활성여부 | Y |
""")

col_u1, col_u2 = st.columns(2)
with col_u1:
    file1 = st.file_uploader("📄 고객 기본정보 파일 (.xlsx / .xls)", type=["xlsx", "xls"], key="f1")
with col_u2:
    file2 = st.file_uploader("📄 고객 거래정보 파일 (.xlsx / .xls)", type=["xlsx", "xls"], key="f2")

if file1 is None or file2 is None:
    st.info("두 파일을 모두 업로드하면 대시보드가 표시됩니다.")
    st.stop()

# ── 로드 ─────────────────────────────────────────────────────────
df1 = load_excel(file1)
df2 = load_excel(file2)

if df1 is None or df2 is None:
    st.stop()

# ── 공통 키 자동 탐지 ─────────────────────────────────────────────
common_cols = set(df1.columns) & set(df2.columns)
id_candidates = [c for c in common_cols if "id" in c.lower() or "ID" in c or "고객" in c]
merge_key = id_candidates[0] if id_candidates else (list(common_cols)[0] if common_cols else None)

if merge_key is None:
    st.error("두 파일 사이에 공통 컬럼이 없어 병합할 수 없습니다.")
    st.stop()

# ── 병합 ─────────────────────────────────────────────────────────
df = pd.merge(df1, df2, on=merge_key, how="inner")

st.success(f"✅ 병합 완료 — 기준 컬럼: **{merge_key}** | 파일1: {len(df1):,}행 / 파일2: {len(df2):,}행 → 병합 결과: **{len(df):,}행**")

st.divider()

# ══════════════════════════════════════════════════════════════════
# 컬럼명 정규화 (유연하게 인식)
# ══════════════════════════════════════════════════════════════════
def find_col(df, *candidates):
    for c in candidates:
        for col in df.columns:
            if c in col:
                return col
    return None

COL_GRADE    = find_col(df, "등급")
COL_ASSET    = find_col(df, "자산")
COL_AGE      = find_col(df, "연령", "나이")
COL_INVEST   = find_col(df, "투자성향")
COL_PRODUCT  = find_col(df, "상품")
COL_RETURN   = find_col(df, "수익률")
COL_BRANCH   = find_col(df, "점포", "지점")
COL_TRADE    = find_col(df, "거래횟수", "거래")
COL_DIGITAL  = find_col(df, "디지털", "플랫폼")
COL_YEAR     = find_col(df, "가입연도", "연도")

# ══════════════════════════════════════════════════════════════════
# KPI 카드
# ══════════════════════════════════════════════════════════════════
kpi_cols = st.columns(4)

kpi_cols[0].metric("총 고객 수", f"{len(df):,}명")

if COL_ASSET:
    avg_asset = pd.to_numeric(df[COL_ASSET], errors="coerce").mean()
    kpi_cols[1].metric("평균 자산", f"{avg_asset:,.0f} 백만원")

if COL_RETURN:
    avg_return = pd.to_numeric(df[COL_RETURN], errors="coerce").mean()
    kpi_cols[2].metric("평균 수익률", f"{avg_return:.2f}%")

if COL_TRADE:
    avg_trade = pd.to_numeric(df[COL_TRADE], errors="coerce").mean()
    kpi_cols[3].metric("평균 거래횟수 (3개월)", f"{avg_trade:.1f}회")

st.divider()

# ══════════════════════════════════════════════════════════════════
# 차트 행 1 — 고객등급 분포 + 투자성향 분포
# ══════════════════════════════════════════════════════════════════
c1, c2 = st.columns(2)

with c1:
    if COL_GRADE:
        st.subheader("고객등급 분포")
        grade_cnt = df[COL_GRADE].value_counts().reset_index()
        grade_cnt.columns = ["등급", "고객수"]
        chart = (
            alt.Chart(grade_cnt)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("등급:N", sort="-y", title="고객등급"),
                y=alt.Y("고객수:Q", title="고객수"),
                color=alt.Color("등급:N", scale=alt.Scale(scheme="purples"), legend=None),
                tooltip=["등급", "고객수"],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=False, domainColor="#e5e7eb")
        )
        st.altair_chart(chart, use_container_width=True)

with c2:
    if COL_INVEST:
        st.subheader("투자성향 분포")
        inv_cnt = df[COL_INVEST].value_counts().reset_index()
        inv_cnt.columns = ["투자성향", "고객수"]
        chart2 = (
            alt.Chart(inv_cnt)
            .mark_arc(innerRadius=55)
            .encode(
                theta=alt.Theta("고객수:Q"),
                color=alt.Color("투자성향:N", scale=alt.Scale(scheme="purpleblue")),
                tooltip=["투자성향", "고객수"],
            )
            .properties(height=280)
        )
        st.altair_chart(chart2, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 차트 행 2 — 주요 상품 + 관리점포별 고객
# ══════════════════════════════════════════════════════════════════
c3, c4 = st.columns(2)

with c3:
    if COL_PRODUCT:
        st.subheader("주요 가입상품 분포")
        prod_cnt = df[COL_PRODUCT].value_counts().reset_index()
        prod_cnt.columns = ["상품", "고객수"]
        chart3 = (
            alt.Chart(prod_cnt)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("고객수:Q", title="고객수"),
                y=alt.Y("상품:N", sort="-x", title="상품"),
                color=alt.Color("상품:N", scale=alt.Scale(scheme="tealblues"), legend=None),
                tooltip=["상품", "고객수"],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=False, domainColor="#e5e7eb")
        )
        st.altair_chart(chart3, use_container_width=True)

with c4:
    if COL_BRANCH:
        st.subheader("관리점포별 고객수")
        branch_cnt = df[COL_BRANCH].value_counts().reset_index()
        branch_cnt.columns = ["점포", "고객수"]
        chart4 = (
            alt.Chart(branch_cnt)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("고객수:Q", title="고객수"),
                y=alt.Y("점포:N", sort="-x", title="점포"),
                color=alt.Color("점포:N", scale=alt.Scale(scheme="orangered"), legend=None),
                tooltip=["점포", "고객수"],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=False, domainColor="#e5e7eb")
        )
        st.altair_chart(chart4, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 차트 행 3 — 연령대별 평균 자산 + 디지털 플랫폼 활성 비율
# ══════════════════════════════════════════════════════════════════
c5, c6 = st.columns(2)

with c5:
    if COL_AGE and COL_ASSET:
        st.subheader("연령대별 평균 자산")
        tmp = df[[COL_AGE, COL_ASSET]].copy()
        tmp[COL_AGE] = pd.to_numeric(tmp[COL_AGE], errors="coerce")
        tmp[COL_ASSET] = pd.to_numeric(tmp[COL_ASSET], errors="coerce")
        tmp = tmp.dropna()
        tmp["연령대"] = (tmp[COL_AGE] // 10 * 10).astype(int).astype(str) + "대"
        age_asset = tmp.groupby("연령대")[COL_ASSET].mean().reset_index()
        age_asset.columns = ["연령대", "평균자산"]
        chart5 = (
            alt.Chart(age_asset)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("연령대:O", title="연령대"),
                y=alt.Y("평균자산:Q", title="평균 자산 (백만원)"),
                tooltip=["연령대", alt.Tooltip("평균자산:Q", format=".1f")],
            )
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=True, gridColor="#f3f4f6", domainColor="#e5e7eb")
        )
        st.altair_chart(chart5, use_container_width=True)

with c6:
    if COL_DIGITAL:
        st.subheader("디지털 플랫폼 활성 비율")
        dig_cnt = df[COL_DIGITAL].value_counts().reset_index()
        dig_cnt.columns = ["활성여부", "고객수"]
        chart6 = (
            alt.Chart(dig_cnt)
            .mark_arc(innerRadius=55)
            .encode(
                theta=alt.Theta("고객수:Q"),
                color=alt.Color(
                    "활성여부:N",
                    scale=alt.Scale(domain=["Y", "N"], range=["#4f46e5", "#e5e7eb"]),
                ),
                tooltip=["활성여부", "고객수"],
            )
            .properties(height=280)
        )
        st.altair_chart(chart6, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 병합 데이터 미리보기 & 다운로드
# ══════════════════════════════════════════════════════════════════
with st.expander("🔍 병합된 원본 데이터 미리보기", expanded=False):
    st.dataframe(df, use_container_width=True, hide_index=True)

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button(
        "⬇ 병합 데이터 다운로드 (.xlsx)",
        data=buf,
        file_name="merged_customers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
