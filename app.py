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
            alloc_df.style.map(color_delta, subset=["Δ (докупить/продать)"])
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
            y=to_float(res.required_capital), line_dash="dash", line_color="green", 
            annotation_text=f"Цель FIRE: {money(res.required_capital)}"
        )
        st.plotly_chart(fig, use_container_width=True)

# ================= ТАБ 5: ДОРОЖНАЯ КАРТА (НОВЫЙ) =================
with tabs[4]:
    st.header("🗺️ Конструктор дорожной карты целей")
    st.markdown("Ваш ориентировочный свободный поток: **~37 900 ₽/мес**. Выберите цели, и мы рассчитаем реалистичный график их достижения.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Параметры бюджета")
        base_flow = st.number_input("Базовый свободный поток (₽/мес)", value=37900, step=500)
        
        st.markdown("**Блок D: Оптимизация расходов**")
        st.markdown("Сколько дополнительно высвободите в месяц за счёт аудита подписок, тарифов и кэшбэка?")
        optimization_savings = st.slider("Доп. экономия в месяц", 0, 10000, 2000, step=500)
        
        total_budget = base_flow + optimization_savings
        st.metric("Итого бюджет на цели", f"{int(total_budget):,} ₽/мес".replace(",", " "), delta=f"+{int(optimization_savings)} ₽ за счёт оптимизации")

    with col2:
        st.subheader("2. Выбор целей")
        st.markdown("*(Алгоритм автоматически выстроит их в оптимальном порядке)*")
        
        short_goals = [k for k, v in GOAL_CATALOG.items() if v["type"] == "short"]
        medium_goals = [k for k, v in GOAL_CATALOG.items() if v["type"] == "medium"]
        long_goals = [k for k, v in GOAL_CATALOG.items() if v["type"] == "long"]
        
        selected = []
        selected.extend(st.multiselect(
            "🛡️ Краткосрочные (Фундамент)", 
            options=short_goals, 
            format_func=lambda x: f"{x}: {GOAL_CATALOG[x]['name']}",
            default=["A2", "A4", "A6"]
        ))
        selected.extend(st.multiselect(
            "📈 Среднесрочные (Рост)", 
            options=medium_goals, 
            format_func=lambda x: f"{x}: {GOAL_CATALOG[x]['name']}",
            default=["B13"]
        ))
        selected.extend(st.multiselect(
            "🏛️ Долгосрочные (Будущее)", 
            options=long_goals, 
            format_func=lambda x: f"{x}: {GOAL_CATALOG[x]['name']}",
            default=[]
        ))
        
        # Убираем дубликаты, сохраняя порядок выбора
        selected = list(dict.fromkeys(selected))

    if selected and total_budget > 0:
        st.divider()
        st.subheader("3. Ваш персональный план")
        
        roadmap = build_roadmap(selected, Decimal(str(total_budget)), Decimal(str(optimization_savings)))
        
        timeline_data = []
        for step in roadmap:
            timeline_data.append({
                "Этап": step.goal_id,
                "Цель": step.goal_name,
                "Сумма": f"{int(step.cost):,} ₽".replace(",", " "),
                "Длительность": f"{step.months_needed} мес.",
                "Финиш": f"через {step.cumulative_months} мес.",
                "Комментарий": step.note
            })
            
        df_timeline = pd.DataFrame(timeline_data)
        st.dataframe(df_timeline, hide_index=True, use_container_width=True)
        
        # График Ганта (упрощённый через Plotly Bar)
        chart_data = []
        current_month = 0
        for step in roadmap:
            chart_data.append({
                "Задача": f"{step.goal_id}: {step.goal_name}",
                "Старт (мес)": current_month,
                "Длительность": step.months_needed,
                "Финиш (мес)": current_month + step.months_needed
            })
            current_month += step.months_needed
            
        df_gantt = pd.DataFrame(chart_data)
        
        fig = px.bar(
            df_gantt, 
            x="Длительность", 
            y="Задача", 
            base="Старт (мес)",
            orientation='h',
            text="Финиш (мес)",
            labels={"Длительность": "Месяцев", "Задача": "Цель", "Финиш (мес)": "Месяц завершения"},
            color="Задача",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_traces(texttemplate="Финиш: мес. %{text}", textposition="outside")
        fig.update_layout(showlegend=False, xaxis_title="Месяцы от начала", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
        
        years = current_month / 12
        st.success(f"✅ При бюджете **{int(total_budget):,} ₽/мес** вы закроете все выбранные цели за **{current_month} месяцев** ({years:.1f} лет).")
    elif not selected:
        st.info("👈 Выберите хотя бы одну цель в меню справа, чтобы построить план.")
