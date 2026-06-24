"""TradingAgents A股分析 — Streamlit Web UI."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# override=True：让 .env 的值优先于进程里可能残留的空/旧环境变量（#66）。
# 注意：load_dotenv 仅在进程启动时执行一次，启动后修改 .env 仍需重启 Web 服务才生效。
load_dotenv(_PROJECT_ROOT / ".env", override=True)

from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402

from web.components.progress_panel import render_progress  # noqa: E402
from web.components.report_viewer import render_report  # noqa: E402
from web.components.sidebar import render_sidebar  # noqa: E402
from web.history import clear_incomplete_task, extract_signal, load_analysis  # noqa: E402
from web.progress import ProgressTracker  # noqa: E402
from web.runner import run_analysis_in_thread  # noqa: E402

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TradingAgents-Astock A股分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Login guard ──────────────────────────────────────────────────────────────

def _parse_users() -> dict[str, dict[str, str]]:
    """Parse LOGIN_USERS env var into {username: {password, role}}."""
    raw = os.getenv("LOGIN_USERS", "")
    users: dict[str, dict[str, str]] = {}
    for entry in raw.split(","):
        parts = entry.strip().split(":")
        if len(parts) == 3:
            uname, passwd, role = parts
            users[uname.strip()] = {"password": passwd.strip(), "role": role.strip()}
    return users


def _check_login() -> None:
    if st.session_state.get("logged_in"):
        return

    st.markdown(
        """
        <style>
        .stApp { background: #f0f2f6 !important; }
        section[data-testid="stSidebar"] { display: none !important; }

        /* Left info panel */
        .login-left-panel {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
            border-radius: 16px;
            padding: 48px 40px;
            color: #fff;
            min-height: 480px;
        }
        .login-left-panel h1 { font-size: 1.7rem; font-weight: 800; margin-bottom: 6px; }
        .login-left-panel h1 span { color: #ff5a1f; }
        .login-left-panel .sub { font-size: 0.85rem; color: #aab; margin-bottom: 32px; }
        .feat { display: flex; gap: 10px; margin-bottom: 16px; font-size: 0.88rem; color: #ccd; line-height: 1.5; }
        .feat-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }
        .login-left-panel .disc { font-size: 0.72rem; color: #778; margin-top: 32px; }

        /* Right login panel */
        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:last-child {
            background: #ffffff;
            border-radius: 16px;
            padding: 32px 28px;
            min-height: 480px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.10);
        }

        /* Override dark input styles for login page */
        .stApp .stTextInput input {
            background: #f7f8fa !important;
            border: 1.5px solid #dde1e9 !important;
            border-radius: 8px !important;
            color: #1a1a2e !important;
            font-size: 0.95rem !important;
            cursor: text !important;
        }
        .stApp .stTextInput input:focus {
            border-color: #ff5a1f !important;
            box-shadow: 0 0 0 2px rgba(255,90,31,0.15) !important;
            background: #fff !important;
        }
        .stApp .stTextInput input::placeholder {
            color: #aab0bb !important;
            opacity: 1 !important;
        }
        .stApp .stTextInput input {
            caret-color: #1a1a2e !important;
        }
        .stApp .stTextInput label {
            color: #555 !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown(
            """
            <div class="login-left-panel">
              <h1>Trading<span>Agents</span><br>-Astock</h1>
              <div class="sub">A股多Agent智能投研系统</div>
              <div class="feat"><span class="feat-icon">🤖</span><span>7个AI分析师角色协同，覆盖市场、情绪、新闻、基本面、政策、游资、解禁多维视角</span></div>
              <div class="feat"><span class="feat-icon">⚔️</span><span>Bull vs Bear辩论 + 三方风险辩论，自动生成结构化投资报告</span></div>
              <div class="feat"><span class="feat-icon">📡</span><span>实时对接东财、腾讯、新浪、同花顺等主流数据源</span></div>
              <div class="feat"><span class="feat-icon">🔍</span><span>支持6位股票代码或中文全称，自动解析分析</span></div>
              <div class="feat"><span class="feat-icon">📄</span><span>分析完成后可导出PDF报告，留存研究记录</span></div>
              <div class="disc">⚠️ 仅供学习研究使用，不构成投资建议</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:1.4rem;font-weight:700;color:#1a1a2e;margin-bottom:8px;letter-spacing:-0.01em'>账号登录</div>"
            "<div style='font-size:0.82rem;color:#888;margin-bottom:28px'>请输入您的账号和密码</div>",
            unsafe_allow_html=True,
        )
        username = st.text_input("账号", placeholder="请输入账号", label_visibility="collapsed")
        password = st.text_input("密码", type="password", placeholder="请输入密码", label_visibility="collapsed")
        if st.button("登 录", use_container_width=True, type="primary"):
            users = _parse_users()
            user = users.get(username)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.rerun()
            else:
                st.error("账号或密码错误")
    st.stop()

_check_login()

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

    /* Hide Streamlit chrome for clean video recording.
       IMPORTANT: do NOT `display:none` the whole header OR the whole toolbar.
       In Streamlit >= 1.36 the "expand sidebar" button lives *inside* the
       toolbar (header > stToolbar > stExpandSidebarButton), so hiding either
       one makes a collapsed sidebar impossible to reopen (issue #36). Instead
       keep the header/toolbar in the DOM, make the header transparent, and
       hide only the individual chrome widgets we don't want on camera. */
    #MainMenu,
    footer,
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    div[data-testid="stToolbarActions"],
    div[data-testid="stAppDeployButton"],
    span[data-testid="stMainMenu"] { display: none !important; }
    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
    }
    /* Keep the sidebar collapse / expand controls always visible & clickable.
       Selector list spans multiple Streamlit versions. */
    button[data-testid="stExpandSidebarButton"],
    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    .stApp {
        background: #0a0a0a;
    }
    section[data-testid="stSidebar"] {
        background: #0f0f0f;
        border-right: 1px solid #1a1a1a;
    }
    .stMetric label { color: #888 !important; font-size: 0.8rem !important; }
    .stMetric [data-testid="stMetricValue"] {
        color: #ff5a1f !important;
        font-weight: 700 !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #ff5a1f, #ff8c42) !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #ff5a1f, #ff8c42) !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 4px 15px rgba(255,90,31,0.3) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #e04d15, #ff5a1f) !important;
        box-shadow: 0 6px 20px rgba(255,90,31,0.4) !important;
        transform: translateY(-1px) !important;
    }
    /* Secondary buttons (history items) */
    button[kind="secondary"] {
        background: #161616 !important;
        border: 1px solid #2a2a2a !important;
        color: #ccc !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        background: #1e1e1e !important;
        border-color: #ff5a1f !important;
        color: #ff5a1f !important;
    }
    .stExpander {
        border: 1px solid #222 !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #888 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ff5a1f !important;
        border-bottom-color: #ff5a1f !important;
    }
    div[data-testid="stDownloadButton"] button {
        background: #1a1a2e !important;
        border: 1px solid #ff5a1f !important;
        color: #ff5a1f !important;
    }
    /* Text input styling */
    input[data-testid="stTextInputRootElement"] input,
    .stTextInput input {
        background: #161616 !important;
        border-color: #2a2a2a !important;
        color: #f5f1eb !important;
    }
    .stTextInput input:focus {
        border-color: #ff5a1f !important;
        box-shadow: 0 0 0 1px #ff5a1f !important;
    }
    /* Date input styling */
    .stDateInput input {
        background: #161616 !important;
        border-color: #2a2a2a !important;
        color: #f5f1eb !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Build config ─────────────────────────────────────────────────────────────

def _build_config() -> dict:
    from pathlib import Path
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = st.session_state.get("llm_provider", "minimax")
    config["deep_think_llm"] = st.session_state.get("deep_think_llm", "MiniMax-M2.7")
    config["quick_think_llm"] = st.session_state.get("quick_think_llm", "MiniMax-M2.7-highspeed")
    # Optional third-party / proxy endpoint. Sidebar input wins, else .env BACKEND_URL.
    backend_url = (st.session_state.get("llm_base_url") or os.getenv("BACKEND_URL") or "").strip()
    config["backend_url"] = backend_url or None
    config["data_vendors"] = {
        "core_stock_apis": "a_stock",
        "technical_indicators": "a_stock",
        "fundamental_data": "a_stock",
        "news_data": "a_stock",
        "signal_data": "a_stock",
    }
    config["max_debate_rounds"] = 1
    config["max_risk_discuss_rounds"] = 1
    config["checkpoint_enabled"] = True
    config["output_language"] = "Chinese"
    # Per-user isolation: results and memory under <base>/<username>/
    username = st.session_state.get("username")
    if username:
        base_results = Path(DEFAULT_CONFIG["results_dir"])
        base_memory = Path(DEFAULT_CONFIG["memory_log_path"]).parent.parent
        config["username"] = username
        config["results_dir"] = str(base_results / username)
        config["memory_log_path"] = str(base_memory / username / "trading_memory.md")
    return config


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    render_sidebar()


# ── Handle "Start Analysis" trigger ──────────────────────────────────────────

start_req = st.session_state.pop("start_analysis", None)
if start_req:
    if start_req.get("fresh"):
        from tradingagents.graph.checkpointer import clear_checkpoint

        clear_incomplete_task(start_req["ticker"], start_req["trade_date"])
        clear_checkpoint(
            DEFAULT_CONFIG["data_cache_dir"],
            start_req["ticker"],
            start_req["trade_date"],
        )

    tracker = ProgressTracker(
        ticker=start_req["ticker"],
        trade_date=start_req["trade_date"],
    )
    st.session_state["tracker"] = tracker
    st.session_state["viewing_history"] = None
    run_analysis_in_thread(
        ticker=start_req["ticker"],
        trade_date=start_req["trade_date"],
        config=_build_config(),
        tracker=tracker,
    )


# ── Main area state machine ─────────────────────────────────────────────────

tracker: ProgressTracker | None = st.session_state.get("tracker")
viewing_history: str | None = st.session_state.get("viewing_history")

# State 1: Viewing a historical analysis
if viewing_history:
    try:
        state = load_analysis(viewing_history)
        signal = extract_signal(state)
        ticker = Path(viewing_history).parent.parent.name
        trade_date = Path(viewing_history).stem.replace("full_states_log_", "")
        render_report(state, ticker, trade_date, signal)
    except Exception as exc:
        st.error(f"加载失败: {exc}")

# State 2: Analysis running
elif tracker and tracker.is_running:
    render_progress(tracker)
    time.sleep(2)
    st.rerun()

# State 3: Analysis complete
elif tracker and tracker.is_complete:
    render_report(
        tracker.final_state,
        tracker.ticker,
        tracker.trade_date,
        tracker.signal,
        elapsed=tracker.elapsed,
    )

# State 4: Analysis errored
elif tracker and tracker.error:
    st.error(f"分析失败: {tracker.error}")
    st.caption("已完成阶段会保存在本地断点中；修复模型额度或配置后，可以继续未完成的部分。")
    if st.button("继续未完成任务", type="primary"):
        st.session_state["start_analysis"] = {
            "ticker": tracker.ticker,
            "trade_date": tracker.trade_date,
        }
        st.session_state["viewing_history"] = None
        st.rerun()

# State 0: Idle — welcome screen
else:
    st.markdown(
        """
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            text-align: center;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📈</div>
            <div style="
                font-size: 2.5rem;
                font-weight: 900;
                margin-bottom: 0.5rem;
            ">
                <span style="color: #ff5a1f;">Trading</span><span style="color: #f5f1eb;">Agents</span><span style="color: #f5f1eb;">-</span><span style="color: #ff5a1f;">Astock</span>
            </div>
            <div style="color: #888; font-size: 1.1rem; max-width: 500px; line-height: 1.6;">
                A股多Agent投研分析系统<br>
                7位AI分析师 → 质量门控 → 多空辩论 → 风控评估 → 最终决策
            </div>
            <div style="
                margin-top: 2rem;
                padding: 1rem 2rem;
                border: 1px solid #222;
                border-radius: 12px;
                color: #666;
                font-size: 0.9rem;
            ">
                ← 在左侧输入股票代码，开始分析
            </div>
            <div style="
                margin-top: 2.5rem;
                padding: 0.8rem 1.5rem;
                color: #555;
                font-size: 0.75rem;
                max-width: 500px;
                line-height: 1.6;
                border-top: 1px solid #1a1a1a;
            ">
                ⚠️ 本项目仅供学习研究与技术演示，不构成任何投资建议。<br>
                投资决策请咨询持牌专业机构。作者不对使用本工具产生的任何损失承担责任。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
