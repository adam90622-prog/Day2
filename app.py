import streamlit as st
import pandas as pd
import altair as alt
import io
import requests
from datetime import datetime

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
.block-container { padding: 2.5rem 3rem 2rem 3rem; max-width: 1300px; }

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

.weather-card {
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    color: white;
    box-shadow: 0 4px 20px rgba(59,130,246,0.3);
}
.weather-temp { font-size: 3rem; font-weight: 800; }
.weather-label { font-size: 0.9rem; opacity: 0.8; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# 서울 날씨 섹션 (open-meteo API)
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_seoul_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 37.5665,
        "longitude": 126.9780,
        "current": "temperature_2m,weathercode",
        "hourly": "temperature_2m",
        "timezone": "Asia/Seoul",
        "forecast_days": 1,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

st.title("🏦 고객 통합 대시보드")
st.caption("두 개의 고객 데이터 파일을 업로드하면 고객ID 기준으로 병합하여 분석합니다.")

st.divider()
st.subheader("🌤 서울 현재 날씨")

try:
    weather = fetch_seoul_weather()
    current_temp = weather["current"]["temperature_2m"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    hourly_times = weather["hourly"]["time"]
    hourly_temps = weather["hourly"]["temperature_2m"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    weather_df = pd.DataFrame({
        "시각": pd.to_datetime(hourly_times),
        "기온(°C)": hourly_temps,
    })
    weather_df = weather_df[weather_df["시각"].dt.strftime("%Y-%m-%d") == today_str].copy()
    weather_df["시각_표시"] = weather_df["시각"].dt.strftime("%H:%M")

    wcol1, wcol2 = st.columns([1, 3])
    with wcol1:
        st.markdown(f"""
<div class="weather-card">
  <div class="weather-label">📍 서울특별시 &nbsp;·&nbsp; {now_str} 기준</div>
  <div class="weather-temp">{current_temp}°C</div>
  <div class="weather-label">현재 기온</div>
</div>
""", unsafe_allow_html=True)

    with wcol2:
        min_t = weather_df["기온(°C)"].min()
        max_t = weather_df["기온(°C)"].max()
        y_min = min_t - 2
        y_max = max_t + 2

        line = (
            alt.Chart(weather_df)
            .mark_line(color="#3b82f6", strokeWidth=2.5)
            .encode(
                x=alt.X("시각_표시:O", title="시각", axis=alt.Axis(labelAngle=-45, tickCount=12)),
                y=alt.Y("기온(°C):Q", title="기온 (°C)",
                        scale=alt.Scale(domain=[y_min, y_max]),
                        axis=alt.Axis(tickCount=6, format=".1f")),
                tooltip=[alt.Tooltip("시각_표시:O", title="시각"), alt.Tooltip("기온(°C):Q", format=".1f", title="기온")],
            )
        )
        points = (
            alt.Chart(weather_df)
            .mark_point(color="#1d4ed8", size=40, filled=True)
            .encode(
                x=alt.X("시각_표시:O"),
                y=alt.Y("기온(°C):Q"),
                tooltip=[alt.Tooltip("시각_표시:O", title="시각"), alt.Tooltip("기온(°C):Q", format=".1f", title="기온")],
            )
        )
        now_hour = datetime.now().strftime("%H:00")
        current_marker_df = weather_df[weather_df["시각_표시"] == now_hour]
        layers = [line, points]
        if not current_marker_df.empty:
            marker = (
                alt.Chart(current_marker_df)
                .mark_point(color="#ef4444", size=120, filled=True, shape="diamond")
                .encode(
                    x=alt.X("시각_표시:O"),
                    y=alt.Y("기온(°C):Q"),
                    tooltip=[alt.Tooltip("시각_표시:O", title="현재"), alt.Tooltip("기온(°C):Q", format=".1f", title="기온")],
                )
            )
            layers.append(marker)

        weather_chart = (
            alt.layer(*layers)
            .properties(height=220, title="오늘 서울 시간별 기온")
            .configure_view(strokeWidth=0)
            .configure_axis(grid=True, gridColor="#e5e7eb", gridDash=[2, 4], domainColor="#d1d5db")
            .configure_title(fontSize=14, color="#374151")
        )
        st.altair_chart(weather_chart, use_container_width=True)

except Exception as e:
    st.warning(f"날씨 정보를 불러오지 못했습니다: {e}")

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
def load_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"파일을 읽을 수 없습니다: {e}")
        return None

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

# ══════════════════════════════════════════════════════════════════
# 컬럼명 정규화
# ══════════════════════════════════════════════════════════════════
def find_col(df, *candidates):
    for c in candidates:
        for col in df.columns:
            if c in col:
                return col
    return None

COL_GRADE   = find_col(df, "등급")
COL_ASSET   = find_col(df, "자산")
COL_AGE     = find_col(df, "연령", "나이")
COL_INVEST  = find_col(df, "투자성향")
COL_PRODUCT = find_col(df, "상품")
COL_RETURN  = find_col(df, "수익률")
COL_BRANCH  = find_col(df, "점포", "지점")
COL_TRADE   = find_col(df, "거래횟수", "거래")
COL_DIGITAL = find_col(df, "디지털", "플랫폼")
COL_YEAR    = find_col(df, "가입연도", "연도")

# ══════════════════════════════════════════════════════════════════
# 사이드바 필터
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔍 데이터 필터")
    st.caption("항목을 선택하면 대시보드 전체에 반영됩니다.")

    df_f = df.copy()

    if COL_GRADE:
        all_grades = sorted(df[COL_GRADE].dropna().unique().tolist())
        sel_grades = st.multiselect("고객등급", all_grades, default=all_grades)
        if sel_grades:
            df_f = df_f[df_f[COL_GRADE].isin(sel_grades)]

    if COL_INVEST:
        all_inv = sorted(df[COL_INVEST].dropna().unique().tolist())
        sel_inv = st.multiselect("투자성향", all_inv, default=all_inv)
        if sel_inv:
            df_f = df_f[df_f[COL_INVEST].isin(sel_inv)]

    if COL_BRANCH:
        all_branch = sorted(df[COL_BRANCH].dropna().unique().tolist())
        sel_branch = st.multiselect("관리점포", all_branch, default=all_branch)
        if sel_branch:
            df_f = df_f[df_f[COL_BRANCH].isin(sel_branch)]

    if COL_PRODUCT:
        all_prod = sorted(df[COL_PRODUCT].dropna().unique().tolist())
        sel_prod = st.multiselect("주요가입상품", all_prod, default=all_prod)
        if sel_prod:
            df_f = df_f[df_f[COL_PRODUCT].isin(sel_prod)]

    if COL_AGE:
        ages = pd.to_numeric(df[COL_AGE], errors="coerce").dropna()
        if not ages.empty:
            age_min, age_max = int(ages.min()), int(ages.max())
            sel_age = st.slider("연령 범위", age_min, age_max, (age_min, age_max))
            df_f = df_f[pd.to_numeric(df_f[COL_AGE], errors="coerce").between(sel_age[0], sel_age[1])]

    st.divider()
    st.caption(f"필터 적용 결과: **{len(df_f):,}명** / 전체 {len(df):,}명")

if df_f.empty:
    st.warning("필터 조건에 해당하는 고객이 없습니다. 필터를 조정해주세요.")
    st.stop()

st.divider()

# ══════════════════════════════════════════════════════════════════
# KPI 카드
# ══════════════════════════════════════════════════════════════════
kpi_cols = st.columns(4)
kpi_cols[0].metric("총 고객 수", f"{len(df_f):,}명")

if COL_ASSET:
    avg_asset = pd.to_numeric(df_f[COL_ASSET], errors="coerce").mean()
    kpi_cols[1].metric("평균 자산", f"{avg_asset:,.0f} 백만원")

if COL_RETURN:
    avg_return = pd.to_numeric(df_f[COL_RETURN], errors="coerce").mean()
    kpi_cols[2].metric("평균 수익률", f"{avg_return:.2f}%")

if COL_TRADE:
    avg_trade = pd.to_numeric(df_f[COL_TRADE], errors="coerce").mean()
    kpi_cols[3].metric("평균 거래횟수 (3개월)", f"{avg_trade:.1f}회")

st.divider()

# ── 공통 차트 스타일 헬퍼 ─────────────────────────────────────────
AXIS_STYLE = dict(grid=False, domainColor="#d1d5db", labelColor="#6b7280", titleColor="#374151")
GRID_STYLE = dict(grid=True, gridColor="#f3f4f6", gridDash=[3, 3], domainColor="#d1d5db",
                  labelColor="#6b7280", titleColor="#374151")

# ══════════════════════════════════════════════════════════════════
# 차트 행 1 — 고객등급 분포 + 투자성향 분포
# ══════════════════════════════════════════════════════════════════
c1, c2 = st.columns(2)

with c1:
    if COL_GRADE:
        st.subheader("고객등급 분포")
        grade_cnt = df_f[COL_GRADE].value_counts().reset_index()
        grade_cnt.columns = ["등급", "고객수"]
        chart = (
            alt.Chart(grade_cnt)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("등급:N", sort="-y", title="고객등급",
                         axis=alt.Axis(labelAngle=0, labelFontSize=12)),
                y=alt.Y("고객수:Q", title="고객수",
                         axis=alt.Axis(tickCount=5, format=",d")),
                color=alt.Color("등급:N", scale=alt.Scale(scheme="purples"), legend=None),
                tooltip=["등급", alt.Tooltip("고객수:Q", format=",d")],
            )
            .properties(height=300)
            .configure_view(strokeWidth=0)
            .configure_axis(**AXIS_STYLE)
        )
        st.altair_chart(chart, use_container_width=True)

with c2:
    if COL_INVEST:
        st.subheader("투자성향 분포")
        inv_cnt = df_f[COL_INVEST].value_counts().reset_index()
        inv_cnt.columns = ["투자성향", "고객수"]
        chart2 = (
            alt.Chart(inv_cnt)
            .mark_arc(innerRadius=60, outerRadius=110)
            .encode(
                theta=alt.Theta("고객수:Q"),
                color=alt.Color("투자성향:N", scale=alt.Scale(scheme="purpleblue"),
                                legend=alt.Legend(orient="right", labelFontSize=12)),
                tooltip=["투자성향", alt.Tooltip("고객수:Q", format=",d")],
            )
            .properties(height=300)
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
        prod_cnt = df_f[COL_PRODUCT].value_counts().reset_index()
        prod_cnt.columns = ["상품", "고객수"]
        chart3 = (
            alt.Chart(prod_cnt)
            .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
            .encode(
                x=alt.X("고객수:Q", title="고객수",
                         axis=alt.Axis(tickCount=5, format=",d")),
                y=alt.Y("상품:N", sort="-x", title=None,
                         axis=alt.Axis(labelFontSize=12)),
                color=alt.Color("상품:N", scale=alt.Scale(scheme="tealblues"), legend=None),
                tooltip=["상품", alt.Tooltip("고객수:Q", format=",d")],
            )
            .properties(height=300)
            .configure_view(strokeWidth=0)
            .configure_axis(**AXIS_STYLE)
        )
        st.altair_chart(chart3, use_container_width=True)

with c4:
    if COL_BRANCH:
        st.subheader("관리점포별 고객수")
        branch_cnt = df_f[COL_BRANCH].value_counts().reset_index()
        branch_cnt.columns = ["점포", "고객수"]
        chart4 = (
            alt.Chart(branch_cnt)
            .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
            .encode(
                x=alt.X("고객수:Q", title="고객수",
                         axis=alt.Axis(tickCount=5, format=",d")),
                y=alt.Y("점포:N", sort="-x", title=None,
                         axis=alt.Axis(labelFontSize=12)),
                color=alt.Color("점포:N", scale=alt.Scale(scheme="orangered"), legend=None),
                tooltip=["점포", alt.Tooltip("고객수:Q", format=",d")],
            )
            .properties(height=300)
            .configure_view(strokeWidth=0)
            .configure_axis(**AXIS_STYLE)
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
        tmp = df_f[[COL_AGE, COL_ASSET]].copy()
        tmp[COL_AGE]   = pd.to_numeric(tmp[COL_AGE],   errors="coerce")
        tmp[COL_ASSET] = pd.to_numeric(tmp[COL_ASSET], errors="coerce")
        tmp = tmp.dropna()
        tmp["연령대"] = (tmp[COL_AGE] // 10 * 10).astype(int).astype(str) + "대"
        age_asset = tmp.groupby("연령대")[COL_ASSET].mean().reset_index()
        age_asset.columns = ["연령대", "평균자산"]
        y_min = age_asset["평균자산"].min() * 0.85
        y_max = age_asset["평균자산"].max() * 1.10

        area = (
            alt.Chart(age_asset)
            .mark_area(opacity=0.15, color="#4f46e5")
            .encode(
                x=alt.X("연령대:O", title="연령대", axis=alt.Axis(labelAngle=0, labelFontSize=12)),
                y=alt.Y("평균자산:Q", scale=alt.Scale(domain=[y_min, y_max]),
                         axis=alt.Axis(tickCount=5, format=",.0f", title="평균 자산 (백만원)")),
            )
        )
        line5 = (
            alt.Chart(age_asset)
            .mark_line(color="#4f46e5", strokeWidth=2.5)
            .encode(
                x=alt.X("연령대:O"),
                y=alt.Y("평균자산:Q", scale=alt.Scale(domain=[y_min, y_max])),
            )
        )
        pts5 = (
            alt.Chart(age_asset)
            .mark_point(color="#4f46e5", size=80, filled=True)
            .encode(
                x=alt.X("연령대:O"),
                y=alt.Y("평균자산:Q", scale=alt.Scale(domain=[y_min, y_max])),
                tooltip=["연령대", alt.Tooltip("평균자산:Q", format=",.0f", title="평균자산(백만원)")],
            )
        )
        labels5 = (
            alt.Chart(age_asset)
            .mark_text(dy=-14, fontSize=11, color="#4f46e5", fontWeight="bold")
            .encode(
                x=alt.X("연령대:O"),
                y=alt.Y("평균자산:Q", scale=alt.Scale(domain=[y_min, y_max])),
                text=alt.Text("평균자산:Q", format=",.0f"),
            )
        )
        chart5 = (
            alt.layer(area, line5, pts5, labels5)
            .properties(height=300)
            .configure_view(strokeWidth=0)
            .configure_axis(**GRID_STYLE)
        )
        st.altair_chart(chart5, use_container_width=True)

with c6:
    if COL_DIGITAL:
        st.subheader("디지털 플랫폼 활성 비율")
        dig_cnt = df_f[COL_DIGITAL].value_counts().reset_index()
        dig_cnt.columns = ["활성여부", "고객수"]
        chart6 = (
            alt.Chart(dig_cnt)
            .mark_arc(innerRadius=60, outerRadius=110)
            .encode(
                theta=alt.Theta("고객수:Q"),
                color=alt.Color(
                    "활성여부:N",
                    scale=alt.Scale(domain=["Y", "N"], range=["#4f46e5", "#e5e7eb"]),
                    legend=alt.Legend(orient="right", labelFontSize=13),
                ),
                tooltip=["활성여부", alt.Tooltip("고객수:Q", format=",d")],
            )
            .properties(height=300)
        )
        st.altair_chart(chart6, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# 병합 데이터 미리보기 & 다운로드
# ══════════════════════════════════════════════════════════════════
with st.expander("🔍 병합된 원본 데이터 미리보기", expanded=False):
    st.dataframe(df_f, use_container_width=True, hide_index=True)

    buf = io.BytesIO()
    df_f.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button(
        "⬇ 병합 데이터 다운로드 (.xlsx)",
        data=buf,
        file_name="merged_customers.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
