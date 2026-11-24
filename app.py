import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from finance_tracker.config import DEFAULT_TARGETS, INVESTED_CLASSES, GOAL_CATALOG
from finance_tracker.models.cashflow import FlowType
from finance_tracker.services.allocation import rebalance
from finance_tracker.services.cashflow import net_position, summarize
from finance_tracker.services.fire import FireParams, plan_fire
from finance_tracker.services.reports import money, pct
from finance_tracker.services.roadmap import build_roadmap
from finance_tracker.storage.excel_io import load_workbook_data
from finance_tracker.storage.json_io import load_project

st.set_page_config(page_title="Finance Tracker", page_icon="📊", layout="wide")

# --- Утилиты ---
def to_float(val) -> float:
    """Безопасное преобразование Decimal в float для графиков."""
    if isinstance(val, Decimal):
        return float(val)
    return float(val or 0)

@st.cache_data
def load_default_data():
    """Загружает пример данных из репозитория."""
    path = Path(__file__).parent / "data" / "sample_data.json"
    if path.exists():
        return load_project(path)
    return {}

def parse_uploaded_file(uploaded_file) -> dict:
    """Парсит загруженный пользователем файл во временное хранилище."""
    temp_path = Path(f"/tmp/{uploaded_file.name}")
    temp_path.write_bytes(uploaded_file.getvalue())
    
    if uploaded_file.name.endswith(".json"):
        return load_project(temp_path)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        raw = load_workbook_data(temp_path)
        raw.setdefault("fire", {})
        return raw
    return {}

# --- Состояние приложения ---
if "data" not in st.session_state:
    st.session_state.data = load_default_data()

# --- Боковая панель ---
with st.sidebar:
    st.header("⚙️ Данные")
    uploaded_file = st.file_uploader("Загрузить JSON или Excel", type=["json", "xlsx", "xls"])
    if uploaded_file:
        parsed = parse_uploaded_file(uploaded_file)
        if parsed:
            st.session_state.data = parsed
            st.success("Данные успешно загружены!")
        else:
            st.error("Не удалось распознать формат файла.")
    
    st.divider()
    st.info("💡 По умолчанию загружены демо-данные из скриншотов книги Excel.")

data = st.session_state.data
if not data:
    st.warning("Нет данных для отображения. Загрузите файл или проверьте `data/sample_data.json`.")
    st.stop()

# --- Вкладки ---
tabs = st.tabs(["🏦 Баланс", "📈 Аллокация", "💸 Доходы/Расходы", "🔥 FIRE-план", "🗺️ Дорожная карта"])

# ================= ТАБ 1: БАЛАНС =================
with tabs[0]:
    st.header("Активы и пассивы")
    balance = data.get("balance")
    if balance:
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Всего активов", money(balance.total_assets()))
        col2.metric("📉 Всего пассивов", money(balance.total_liabilities()))
        col3.metric("🏆 Чистый капитал", money(balance.net_worth()))

        asset_df = pd.DataFrame([
            {"Класс": a.asset_class.ru_label, "Стоимость": to_float(a.value), "Актив": a.name}
            for a in balance.assets
        ])
        if not asset_df.empty:
            fig = px.pie(asset_df, values="Стоимость", names="Класс", hover_data=["Актив"], hole=0.4)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Детализация активов")
        st.dataframe(asset_df, hide_index=True, use_container_width=True)

# ================= ТАБ 2: АЛЛОКАЦИЯ =================
with tabs[1]:
    st.header("Целевая аллокация инвестиционного ядра")
    balance = data.get("balance")
    if balance:
        actions = rebalance(balance, DEFAULT_TARGETS)
        alloc_df = pd.DataFrame([
            {
                "Класс": a.asset_class.ru_label,
                "Цель": pct(a.target_share),
                "Текущее": to_float(a.current),
                "Рекомендуется": to_float(a.recommended),
                "Δ (докупить/продать)": to_float(a.delta),
                "Действие": a.action
            }
            for a in actions
        ])
        
        def color_delta(val):
            if val > 1: return "color: green; font-weight: bold"
            if val < -1: return "color: red; font-weight: bold"
            return "color: gray"
            
        st.dataframe(
            alloc_df.style.applymap(color_delta, subset=["Δ (докупить/продать)"]), 
            hide_index=True, use_container_width=True
        )
        
        fig = px.bar(
            alloc_df, x="Класс", y=["Текущее", "Рекомендуется"], barmode="group", 
            labels={"value": "Сумма (₽)", "variable": "Состояние"},
            color_discrete_sequence=["#636EFA", "#EF553B"]
        )
        st.plotly_chart(fig, use_container_width=True)

# ================= ТАБ 3: ДОХОДЫ / РАСХОДЫ =================
with tabs[2]:
    st.header("Денежные потоки (План vs Факт)")
    income = data.get("income")
    expense = data.get("expense")
    
    col1, col2 = st.columns(2)
    if income:
        inc_df = pd.DataFrame([
            {"Категория": r.category, "Название": r.name, "План": to_float(r.planned), "Факт": to_float(r.actual)}
            for r in income.records
        ])
        col1.subheader("📥 Доходы")
        col1.dataframe(inc_df, hide_index=True, use_container_width=True)
        
    if expense:
        exp_df = pd.DataFrame([
            {"Категория": r.category, "Название": r.name, "План": to_float(r.planned), "Факт": to_float(r.actual)}
            for r in expense.records
        ])
        col2.subheader("📤 Расходы")
        col2.dataframe(exp_df, hide_index=True, use_container_width=True)

    if income and expense:
        net = net_position(income, expense)
        st.metric(
            "Чистый денежный поток (факт за месяц)", 
            money(Decimal(str(net))), 
            delta="Положительно 🟢" if net > 0 else "Отрицательно 🔴"
        )

# ================= ТАБ 4: FIRE-ПЛАН =================
with tabs[3]:
    st.header("🔥 FIRE-планировщик (Финансовая независимость)")
    fire_cfg = data.get("fire", {})
    balance = data.get("balance")
    
    current_invested = fire_cfg.get("current_invested")
    if current_invested is None and balance is not None:
        current_invested = str(balance.invested_value(INVESTED_CLASSES))
    
    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.number_input("Ежемесячный доход (₽)", value=float(fire_cfg.get("monthly_income", 43446)), step=1000.0)
        annual_rate = st.number_input("Ожидаемая годовая доходность (%)", value=float(fire_cfg.get("annual_rate", 0.21)) * 100, step=0.5) / 100
    with col2:
        contrib_share = st.number_input("Доля дохода на пополнение (%)", value=float(fire_cfg.get("contribution_share", 0.10)) * 100, step=1.0) / 100
        current_inv = st.number_input("Уже инвестировано (₽)", value=float(current_invested or 0), step=1000.0)

    if st.button("🔄 Рассчитать FIRE-план", type="primary"):
        params = FireParams(
            monthly_income=Decimal(str(monthly_income)),
            annual_rate=Decimal(str(annual_rate)),
            contribution_share=Decimal(str(contrib_share)),
            current_invested=Decimal(str(current_inv)),
            retirement_date=date(2028, 11, 24), # Можно вынести в отдельный input при желании
            today=date.today()
        )
        res = plan_fire(params)
        
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Требуемый капитал", money(res.required_capital))
        c2.metric("Текущий прогресс", pct(res.progress))
        c3.metric("Нужно докидывать в день", money(res.daily_topup))
        c4.metric("Нехватка к цели", money(res.shortfall))
        
        chart_data = []
        for y_no, y_with in zip(res.growth_no_contrib, res.growth_with_contrib):
            chart_data.append({
                "Год": y_no.year,
                "Без пополнений": to_float(y_no.end),
                "С пополнениями": to_float(y_with.end)
            })
        chart_df = pd.DataFrame(chart_data)
        
        fig = px.line(
            chart_df, x="Год", y=["Без пополнений", "С пополнениями"], 
            markers=True, labels={"value": "Капитал (₽)", "variable": "Сценарий"}
        )
        fig.add_hline(
           
