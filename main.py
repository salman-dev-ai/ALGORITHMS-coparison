from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.algorithms import ALGORITHMS
from core.csv_loader import load_processes, template_csv
from core.models import Process

st.set_page_config(
    page_title="Algorithm Comparison Dashboard", page_icon="📊", layout="wide"
)

TEXT = {
    "ar": {
        "title": "لوحة مقارنة خوارزميات جدولة العمليات",
         "language": "اللغة",
        "arabic": "العربية",
        "english": "English",
        "source": "مصدر البيانات",
        "upload": "استيراد ملف CSV",
        "load": "تحميل الملف",
        "template": "تنزيل قالب CSV",
        "settings": "الإعدادات",
        "quantum": "Time Quantum لخوارزمية Round Robin",
        "algorithms": "الخوارزميات",
        "clear": "مسح النتائج",
        "processes": "العمليات",
        "run": "تشغيل المقارنة",
        "choose": "اختر خوارزمية واحدة على الأقل.",
        "success_load": "تم تحميل العمليات بنجاح",
        "comparison": "المقارنة الرقمية",
        "recommend": "مقياس التوصية",
        "best": "وفقًا لـ {metric}، الأفضل لهذه العمليات هو: **{winner}**",
        "details": "تفاصيل {name}",
        "gantt": "مخطط Gantt — {name}",
        "empty": "أدخل العمليات أو استورد CSV ثم اضغط تشغيل المقارنة.",
        "invalid": "يرجى تصحيح البيانات قبل التشغيل.",
        "metric_wait": "متوسط وقت الانتظار",
        "metric_turn": "متوسط زمن الدوران",
        "metric_response": "متوسط زمن الاستجابة",
        "metric_switch": "تبديلات السياق",
        "metric_idle": "وقت الخمول",
        "algorithm": "الخوارزمية",
        "process": "العملية",
        "start": "وقت البداية",
        "duration": "المدة",
        "time": "الزمن",
    },
    "en": {
        "title": "Algorithm Comparison Dashboard",
        "subtitle": "Interactive academic comparison without a database",
        "language": "Language",
        "arabic": "العربية",
        "english": "English",
        "source": "Data Source",
        "upload": "Import CSV file",
        "load": "Load file",
        "template": "Download CSV template",
        "settings": "Settings",
        "quantum": "Time Quantum for Round Robin",
        "algorithms": "Algorithms",
        "clear": "Clear results",
        "processes": "Processes",
        "run": "Run comparison",
        "choose": "Select at least one algorithm.",
        "success_load": "Processes loaded successfully",
        "comparison": "Numerical comparison",
        "recommend": "Recommendation metric",
        "best": "According to {metric}, the best algorithm for this data is: **{winner}**",
        "details": "{name} details",
        "gantt": "Gantt Chart — {name}",
        "empty": "Enter processes or import a CSV, then run the comparison.",
        "invalid": "Please correct the data before running.",
        "metric_wait": "Average Waiting Time",
        "metric_turn": "Average Turnaround Time",
        "metric_response": "Average Response Time",
        "metric_switch": "Context Switches",
        "metric_idle": "Idle Time",
        "algorithm": "Algorithm",
        "process": "Process",
        "start": "Start",
        "duration": "Duration",
        "time": "Time",
    },
}

if "language" not in st.session_state:
    st.session_state.language = "ar"
if "process_df" not in st.session_state:
    st.session_state.process_df = pd.DataFrame(
        [
            {"process_id": "P1", "arrival_time": 0, "burst_time": 8, "priority": 2},
            {"process_id": "P2", "arrival_time": 1, "burst_time": 4, "priority": 1},
            {"process_id": "P3", "arrival_time": 2, "burst_time": 2, "priority": 3},
            {"process_id": "P4", "arrival_time": 3, "burst_time": 6, "priority": 2},
        ]
    )
if "results" not in st.session_state:
    st.session_state.results = {}

with st.sidebar:
    language = st.radio(
        TEXT[st.session_state.language]["language"],
        ["العربية", "English"],
        index=0 if st.session_state.language == "ar" else 1,
    )
    new_language = "ar" if language == "العربية" else "en"
    if new_language != st.session_state.language:
        st.session_state.language = new_language
        st.rerun()

lang = TEXT[st.session_state.language]
st.markdown(
    f"<style>.stApp {{ background:#0b1220; color:#e5e7eb; }} [data-testid='stSidebar'] {{ background:#111827; }} [data-testid='stMetric'] {{ background:#172033; border:1px solid #26344d; border-radius:12px; padding:12px; }} </style><div dir='{ 'rtl' if st.session_state.language == 'ar' else 'ltr' }'></div>",
    unsafe_allow_html=True,
)
st.title("📊 " + lang["title"])
 
with st.sidebar:
    st.header(lang["source"])
    uploaded = st.file_uploader(lang["upload"], type=["csv"])
    if uploaded is not None and st.button(lang["load"], width="stretch"):
        records, errors = load_processes(uploaded.getvalue())
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state.process_df = pd.DataFrame(records)
            st.session_state.results = {}
            st.success(lang["success_load"])
    st.download_button(
        lang["template"],
        template_csv(),
        "processes_template.csv",
        "text/csv",
        width="stretch",
    )
    st.divider()
    st.header(lang["settings"])
    quantum = st.number_input(lang["quantum"], min_value=1, value=2, step=1)
    selected = st.multiselect(
        lang["algorithms"], list(ALGORITHMS), default=list(ALGORITHMS)
    )
    if st.button(lang["clear"], width="stretch"):
        st.session_state.results = {}
        st.rerun()

st.subheader(lang["processes"])
edited = st.data_editor(
    st.session_state.process_df,
    num_rows="dynamic",
    width="stretch",
    hide_index=True,
    key="process_editor",
)
st.session_state.process_df = edited

if st.button(lang["run"], type="primary", width="stretch"):
    records, errors = load_processes(edited.to_csv(index=False).encode("utf-8"))
    if errors:
        for error in errors:
            st.error(error)
    elif not selected:
        st.warning(lang["choose"])
    else:
        processes = [
            Process(
                r["process_id"],
                int(r["arrival_time"]),
                int(r["burst_time"]),
                int(r["priority"]),
            )
            for r in records
        ]
        st.session_state.results = {
            name: (
                ALGORITHMS[name](processes, int(quantum))
                if name == "Round Robin"
                else ALGORITHMS[name](processes)
            )
            for name in selected
        }

results = st.session_state.results
if results:
    st.subheader(lang["comparison"])
    labels = {
        "Average Waiting Time": lang["metric_wait"],
        "Average Turnaround Time": lang["metric_turn"],
        "Average Response Time": lang["metric_response"],
        "Context Switches": lang["metric_switch"],
        "Idle Time": lang["metric_idle"],
    }
    summary = pd.DataFrame(
        [
            {
                lang["algorithm"]: name,
                lang["metric_wait"]: result.average_waiting_time,
                lang["metric_turn"]: result.average_turnaround_time,
                lang["metric_response"]: result.average_response_time,
                lang["metric_switch"]: result.context_switches,
                lang["metric_idle"]: result.idle_time,
            }
            for name, result in results.items()
        ]
    )
    st.dataframe(summary.round(2), width="stretch", hide_index=True)
    metric = st.selectbox(
        lang["recommend"],
        [lang["metric_wait"], lang["metric_turn"], lang["metric_response"]],
    )
    winner = summary.loc[summary[metric].idxmin(), lang["algorithm"]]
    st.success(lang["best"].format(metric=metric, winner=winner))
    chart = summary.melt(
        id_vars=lang["algorithm"],
        value_vars=[lang["metric_wait"], lang["metric_turn"], lang["metric_response"]],
        var_name="Metric",
        value_name="Value",
    )
    st.plotly_chart(
        px.bar(
            chart,
            x=lang["algorithm"],
            y="Value",
            color="Metric",
            barmode="group",
            template="plotly_dark",
            title=lang["comparison"],
        ),
        width="stretch",
    )
    for name, result in results.items():
        with st.expander(
            lang["details"].format(name=name), expanded=(name == list(results)[0])
        ):
            st.dataframe(
                pd.DataFrame([vars(p) for p in result.processes]),
                width="stretch",
                hide_index=True,
            )
            if result.timeline:
                figure = go.Figure()
                for item in result.timeline:
                    color = (
                        "#64748b"
                        if item.process_id == "IDLE"
                        else px.colors.qualitative.Set2[
                            hash(item.process_id) % len(px.colors.qualitative.Set2)
                        ]
                    )
                    figure.add_trace(
                        go.Bar(
                            name=item.process_id,
                            y=[item.process_id],
                            x=[item.duration],
                            base=[item.start_time],
                            orientation="h",
                            marker_color=color,
                            hovertemplate=f"{item.process_id}<br>{lang['start']}: {item.start_time}<br>{lang['duration']}: {item.duration}<extra></extra>",
                            showlegend=False,
                        )
                    )
                figure.update_layout(
                    template="plotly_dark",
                    barmode="overlay",
                    title=lang["gantt"].format(name=name),
                    xaxis_title=lang["time"],
                    yaxis_title=lang["process"],
                    height=max(
                        260, 70 + 45 * len(set(s.process_id for s in result.timeline))
                    ),
                    showlegend=False,
                )
                st.plotly_chart(figure, width="stretch")
else:
    st.info(lang["empty"])
