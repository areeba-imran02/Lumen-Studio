"""Writify Studio - Research. Write. Verify. (CrewAI + Gemini + DuckDuckGo + Streamlit)."""
import html
import io
import os
import re
import sys
import time
import zipfile
import datetime as dt
from urllib.parse import quote_plus, urlparse

try:  # Streamlit Cloud ships an old sqlite3; crewai needs a newer one
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from crew_setup import (CUSTOM_LANG, LANGUAGES, LENGTHS, MODELS, OUTPUTS, TONES,  # noqa: E402
                        plan_steps, resolve_outputs, run_studio)

st.set_page_config(page_title="Writify Studio | Research. Write. Verify.", page_icon=":material/auto_awesome:", layout="wide")

# ------------------------------------------------------------------ theme
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* =========================================================
   WRITIFY STUDIO — CLEAN EDITORIAL SAAS UI
   UI ONLY — NO BACKEND / LOGIC CHANGES
   ========================================================= */

:root {
    --ink: #17352F;
    --ink-soft: #52706A;
    --teal-950: #073B35;
    --teal-900: #0A4D45;
    --teal-800: #0B6258;
    --teal-700: #0D766B;
    --mint: #DDF4EC;
    --mint-soft: #F3FAF7;
    --cream: #FCFBF7;
    --line: #D7E8E2;
    --orange: #E86F32;
    --orange-dark: #C95720;
    --white: #FFFFFF;
}

/* ---------- APP ---------- */

.stApp {
    background:
        radial-gradient(circle at 88% 5%, rgba(185, 232, 218, .34), transparent 24%),
        linear-gradient(180deg, #F6FBF8 0%, #FBFCF9 52%, #F7FAF8 100%) !important;
    color: var(--ink) !important;
}

header[data-testid="stHeader"] {
    background: rgba(247, 251, 249, .94) !important;
    backdrop-filter: blur(12px) !important;
    border-bottom: 1px solid #E1ECE8 !important;
    box-shadow: none !important;
}

#MainMenu,
footer {
    visibility: hidden;
}

.block-container {
    max-width: 1160px !important;
    padding-top: 3.8rem !important;
    padding-bottom: 4rem !important;
}

.stApp p,
.stApp li,
.stApp label,
.stApp input,
.stApp textarea,
.stApp button,
.stApp td,
.stApp th {
    font-family: "DM Sans", sans-serif;
}

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    font-family: "Plus Jakarta Sans", sans-serif;
    letter-spacing: -.02em;
}

.stApp p,
.stApp li,
.stApp span {
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}

[data-testid="stCaptionContainer"] {
    color: var(--ink-soft) !important;
}

.stApp [data-testid="stWidgetLabel"] p {
    color: var(--ink) !important;
    font-weight: 700 !important;
}

/* =========================================================
   SIDEBAR
   ========================================================= */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #073B35 0%, #084B43 48%, #0A5D53 100%) !important;
    border-right: 1px solid rgba(255,255,255,.08);
    box-shadow: 8px 0 30px rgba(7,59,53,.13);
}

section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: transparent !important;
}

section[data-testid="stSidebar"] .block-container,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1.25rem !important;
}

section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] label p {
    color: #E8F8F3 !important;
    font-weight: 600 !important;
    font-size: .84rem !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #B8DED4 !important;
}

/* brand */

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 4px;
}

.brand .logo {
    width: 38px;
    height: 38px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 11px;
    background: #CDEFE4;
    color: #075449;
    font-family: "Plus Jakarta Sans", sans-serif;
    font-size: 1.05rem;
    font-weight: 800;
    box-shadow: 0 7px 18px rgba(0,0,0,.15);
}

.brand .bname {
    font-family: "Plus Jakarta Sans", sans-serif;
    font-size: 1.28rem;
    font-weight: 800;
    letter-spacing: -.035em;
    white-space: nowrap;
}

.brand .w3a {
    color: #FFFFFF !important;
}

.brand .w3b {
    color: #AEE3D5 !important;
}

.brand-sub {
    color: #A9D9CE !important;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin: 7px 0 22px;
    padding-bottom: 18px;
    border-bottom: 1px solid rgba(255,255,255,.13);
}

.side-h {
    color: #9FE0D1 !important;
    font-size: .68rem;
    font-weight: 800;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin: 19px 0 7px;
}

/* sidebar inputs */

section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="base-input"] {
    background: rgba(255,255,255,.97) !important;
    border: 1px solid #9BD9CA !important;
    border-radius: 9px !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] input {
    color: #123F38 !important;
    -webkit-text-fill-color: #123F38 !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] svg {
    fill: #0A5D53 !important;
}

section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
    border: none !important;
    background: transparent !important;
}

/* status */

.status {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 9px 12px;
    border-radius: 9px;
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.13);
    color: #F1FFFA !important;
    font-size: .82rem;
    font-weight: 600;
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.dot.ok {
    background: #5BE49A;
    box-shadow: 0 0 0 4px rgba(91,228,154,.13);
}

.dot.bad {
    background: #FF7A7A;
}

.side-note {
    color: #B9DED4 !important;
    font-size: .82rem;
}

section[data-testid="stSidebar"] button {
    border-radius: 8px !important;
}

section[data-testid="stSidebar"] button p {
    color: #E9F8F4 !important;
    font-size: .8rem !important;
}

/* =========================================================
   HERO
   ========================================================= */

.hero {
    position: relative;
    overflow: hidden;
    border-radius: 24px;
    padding: 40px 44px 36px;
    margin-bottom: 26px;

    background:
        radial-gradient(
            460px 260px at 92% 0%,
            rgba(83, 202, 179, .30),
            transparent 68%
        ),
        linear-gradient(135deg, #073B35 0%, #0A5A50 56%, #0B7569 100%);

    box-shadow: 0 18px 42px rgba(7,59,53,.16);
}

.hero .eyebrow {
    color: #A9E5D7 !important;
    font-size: .70rem;
    font-weight: 800;
    letter-spacing: .15em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.hero .hero-title {
    color: #FFFFFF !important;
    font-family: "Plus Jakarta Sans", sans-serif !important;
    font-size: 3.05rem !important;
    font-weight: 800 !important;
    letter-spacing: -.045em !important;
    line-height: 1.08 !important;
    margin: 0 0 12px !important;
}

.hero .hero-title .w3a {
    color: #FFFFFF !important;
    text-shadow: none !important;
}

.hero .hero-title .w3b {
    color: #A9E5D7 !important;
    text-shadow: none !important;
}

.hero .hero-tag {
    color: #E3F7F1 !important;
    font-family: "Plus Jakarta Sans", sans-serif !important;
    font-size: 1.13rem !important;
    font-weight: 700 !important;
    margin: 0 0 7px !important;
}

.hero p {
    color: #CBE8E1 !important;
    max-width: 735px;
    font-size: .96rem;
    line-height: 1.65;
    margin: 0;
}

.hero .feat {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0;
    margin-top: 25px;
    padding-top: 17px;
    border-top: 1px solid rgba(255,255,255,.15);
}

.hero .feat span {
    color: #DDF3ED !important;
    font-size: .78rem;
    font-weight: 600;
    line-height: 1.2;
    padding: 3px 15px;
    border-left: 1px solid rgba(255,255,255,.18);
}

.hero .feat span:first-child {
    padding-left: 0;
    border-left: none;
}

/* =========================================================
   WARNING / NOTE
   ========================================================= */

.stAlert {
    border-radius: 12px !important;
}

.note {
    margin-top: 20px;
    background: #F0F8F5;
    border: 1px solid #CFE4DD;
    border-left: 4px solid #0B7569;
    border-radius: 12px;
    padding: 13px 17px;
    color: #315850;
    font-size: .88rem;
}

/* =========================================================
   MAIN INPUT CARD
   ========================================================= */

.st-key-input_card {
    background: rgba(255,255,255,.94) !important;
    border: 1px solid #D9E9E4 !important;
    border-radius: 20px !important;
    padding: 27px 30px 23px !important;
    box-shadow: 0 12px 35px rgba(20,71,61,.07) !important;
}

.section-title {
    color: #173F38 !important;
    font-family: "Plus Jakarta Sans", sans-serif !important;
    font-size: 1.08rem;
    font-weight: 800;
    letter-spacing: -.02em;
    margin: 2px 0 7px;
}

.hint {
    color: #607B75 !important;
    font-size: .83rem;
    font-weight: 500;
}

.hint-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 9px;
    margin: 0 0 13px;
}

.badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    background: #E8F6F1 !important;
    border: 1px solid #CBE7DE;
    color: #23675C !important;
    font-size: .70rem;
    font-weight: 700;
}

.count {
    display: inline-flex;
    align-items: center;
    height: 2.45rem;
    padding: 0 14px;
    border-radius: 999px;
    background: #EDF7F4;
    border: 1px solid #CDE6DE;
    color: #21675C !important;
    font-size: .79rem;
    font-weight: 800;
    white-space: nowrap;
}

.divider {
    height: 1px;
    background: #E4EFEB;
    margin: 23px 0 21px;
}

/* =========================================================
   TEXT INPUTS
   ========================================================= */

.st-key-input_card [data-testid="stTextArea"] div,
.st-key-input_card [data-testid="stTextInput"] div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.st-key-input_card textarea,
.st-key-input_card [data-testid="stTextInput"] input {
    background: #FBFDFC !important;
    color: #173F38 !important;
    -webkit-text-fill-color: #173F38 !important;
    border: 1.5px solid #C9DDD7 !important;
    border-radius: 11px !important;
    padding: 12px 14px !important;
    font-size: .94rem !important;
    font-weight: 500 !important;
    line-height: 1.55 !important;
    box-shadow: none !important;
    transition: border .15s ease, box-shadow .15s ease, background .15s ease;
}

.st-key-input_card textarea:focus,
.st-key-input_card [data-testid="stTextInput"] input:focus {
    background: #FFFFFF !important;
    border-color: #0B7569 !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(11,117,105,.10) !important;
}

.st-key-input_card textarea::placeholder,
.st-key-input_card input::placeholder {
    color: #78918B !important;
    -webkit-text-fill-color: #78918B !important;
    opacity: 1 !important;
}

/* =========================================================
   EXAMPLE BUTTONS
   ========================================================= */

.st-key-examples [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

.st-key-examples [data-testid="stColumn"],
.st-key-examples [data-testid="column"] {
    width: auto !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
}

.st-key-examples [data-testid="stElementContainer"],
.st-key-examples div.stButton {
    width: auto !important;
}

.st-key-examples button {
    width: auto !important;
    min-height: 2.15rem !important;
    padding: 3px 14px !important;
    border-radius: 999px !important;
    background: #F3F8F6 !important;
    border: 1px solid #D1E4DE !important;
}

.st-key-examples button p {
    color: #38645C !important;
    font-size: .77rem !important;
    font-weight: 600 !important;
}

.st-key-examples button:hover {
    background: #E5F3EE !important;
    border-color: #9DCFC2 !important;
}

/* =========================================================
   DELIVERABLE CHIPS
   ========================================================= */

.st-key-chips [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 10px !important;
}

.st-key-chips [data-testid="stColumn"],
.st-key-chips [data-testid="column"] {
    width: 100% !important;
    min-width: 0 !important;
    flex: none !important;
}

.st-key-chips [data-testid="stElementContainer"],
.st-key-chips div.stButton,
.st-key-chips [data-testid="stButton"] {
    width: 100% !important;
}

.st-key-chips button {
    width: 100% !important;
    min-height: 2.85rem !important;
    border-radius: 10px !important;
    font-size: .82rem !important;
    transition: all .15s ease !important;
}

.st-key-chips button p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-weight: 700 !important;
}

.st-key-chips button[kind="secondary"],
.st-key-chips button[data-testid="stBaseButton-secondary"] {
    background: #FFFFFF !important;
    border: 1.5px solid #C9DED8 !important;
    color: #315E56 !important;
}

.st-key-chips button[kind="secondary"] p {
    color: #315E56 !important;
}

.st-key-chips button[kind="secondary"]:hover {
    background: #F0F8F5 !important;
    border-color: #70B9A8 !important;
}

.st-key-chips button[kind="primary"],
.st-key-chips button[data-testid="stBaseButton-primary"] {
    background: #0A5D53 !important;
    border: 1.5px solid #0A5D53 !important;
    box-shadow: 0 5px 14px rgba(10,93,83,.16) !important;
}

.st-key-chips button[kind="primary"] p {
    color: #FFFFFF !important;
}

/* check mark for selected deliverables */

.st-key-chips button[kind="primary"] p::before,
.st-key-chips button[data-testid="stBaseButton-primary"] p::before {
    content: "\\2713\\00a0";
}

/* =========================================================
   SELECT ALL / CLEAR / GENERATE
   ========================================================= */

.st-key-chip_tools {
    margin-top: 20px;
    padding-top: 19px;
    border-top: 1px solid #E4EFEB;
}

.st-key-chip_tools [data-testid="stHorizontalBlock"] {
    display: grid !important;
    grid-template-columns: 118px 100px auto minmax(0,1fr) 235px !important;
    gap: 10px !important;
    align-items: center !important;
}

.st-key-chip_tools [data-testid="stColumn"],
.st-key-chip_tools [data-testid="column"] {
    width: 100% !important;
    min-width: 0 !important;
    flex: none !important;
}

.st-key-chip_tools [data-testid="stElementContainer"],
.st-key-chip_tools div.stButton {
    width: 100% !important;
}

.st-key-sel_all button,
.st-key-sel_none button {
    width: 100% !important;
    min-height: 2.45rem !important;
    border-radius: 8px !important;
    font-size: .74rem !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: .04em;
    box-shadow: none !important;
}

.st-key-sel_all button {
    background: #173F38 !important;
    border: 1px solid #173F38 !important;
}

.st-key-sel_all button p {
    color: #FFFFFF !important;
}

.st-key-sel_none button {
    background: #FFFFFF !important;
    border: 1px solid #D8C4C4 !important;
}

.st-key-sel_none button p {
    color: #8B5555 !important;
}

.st-key-sel_none button:hover {
    background: #FAF2F2 !important;
}

.st-key-go_wrap,
.st-key-go_wrap [data-testid="stElementContainer"],
.st-key-go_wrap [data-testid="stButton"],
.st-key-go_wrap div.stButton {
    width: 100% !important;
}

.st-key-go_wrap button {
    width: 100% !important;
    min-height: 2.8rem !important;
    border-radius: 10px !important;
    background: var(--orange) !important;
    border: 1px solid var(--orange) !important;
    box-shadow: 0 7px 18px rgba(232,111,50,.22) !important;
}

.st-key-go_wrap button:hover {
    background: var(--orange-dark) !important;
    border-color: var(--orange-dark) !important;
}

.st-key-go_wrap button p {
    color: #FFFFFF !important;
    font-family: "Plus Jakarta Sans", sans-serif !important;
    font-size: .87rem !important;
    font-weight: 800 !important;
}

.st-key-go_wrap button:disabled {
    background: #B6C3BF !important;
    border-color: #B6C3BF !important;
    box-shadow: none !important;
}

/* =========================================================
   GENERAL BUTTONS
   ========================================================= */

button[kind="secondary"],
button[data-testid="stBaseButton-secondary"] {
    color: #234E47 !important;
}

button:disabled {
    opacity: .55 !important;
}

/* =========================================================
   PIPELINE
   ========================================================= */

.pipe {
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
    margin: 18px 0 8px;
}

.step {
    flex: 1;
    min-width: 145px;
    padding: 12px 14px;
    border-radius: 11px;
    background: #F8FBFA;
    border: 1px solid #DDEAE6;
    color: #68817B !important;
    font-size: .74rem;
    font-weight: 600;
}

.step b {
    display: block;
    margin-bottom: 4px;
    color: #335B53 !important;
    font-family: "Plus Jakarta Sans", sans-serif;
    font-size: .78rem;
    font-weight: 800;
}

.step.done {
    background: #ECF8F3;
    border-color: #B8DDD1;
    color: #28705F !important;
}

.step.done b {
    color: #1F6556 !important;
}

.step.active {
    background: #FFF5ED;
    border-color: #E9A77E;
    color: #8C512E !important;
    animation: pipelinePulse 1.5s infinite;
}

.step.active b {
    color: #914D28 !important;
}

.step.wait {
    opacity: 1 !important;
}

@keyframes pipelinePulse {
    0% {
        box-shadow: 0 0 0 0 rgba(232,111,50,.18);
    }
    100% {
        box-shadow: 0 0 0 9px rgba(232,111,50,0);
    }
}

/* =========================================================
   RESULTS HEADER
   ========================================================= */

.result-head {
    color: #173F38 !important;
    font-family: "Plus Jakarta Sans", sans-serif !important;
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -.035em;
    margin: 34px 0 12px;
}

.result-head span {
    color: #4C756C !important;
    font-weight: 600;
}

/* =========================================================
   RESULT META BAR
   ========================================================= */

.runbar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 17px;
}

.runbar span {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 12px;
    border-radius: 8px;
    background: #EDF5F2;
    border: 1px solid #D8E8E3;
    color: #41645D !important;
    font-size: .76rem;
    font-weight: 600;
}

.runbar b {
    color: #0A5D53 !important;
    font-family: "Plus Jakarta Sans", sans-serif;
    font-weight: 800;
}

/* =========================================================
   RESULT TABS
   ========================================================= */

.stTabs [data-baseweb="tab-list"] {
    gap: 5px;
    border-bottom: 1px solid #D8E6E1;
    padding-bottom: 0;
}

.stTabs [data-baseweb="tab"] {
    height: auto !important;
    padding: 9px 15px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 8px 8px 0 0 !important;
}

.stTabs [data-baseweb="tab"] p {
    color: #68817B !important;
    font-size: .82rem !important;
    font-weight: 700 !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: #EFF7F4 !important;
}

.stTabs [aria-selected="true"] {
    background: #EAF5F1 !important;
    border-color: #CFE3DC !important;
    border-bottom-color: #EAF5F1 !important;
}

.stTabs [aria-selected="true"] p {
    color: #0A5D53 !important;
    font-weight: 800 !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: #0A7569 !important;
    height: 2px !important;
}

.stTabs [data-baseweb="tab-border"] {
    display: none;
}

.stTabs [data-baseweb="tab-panel"] {
    padding-top: 14px;
}

/* =========================================================
   STAT STRIP
   ========================================================= */

.statstrip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    margin: 5px 0 15px;
    overflow: hidden;
    background: #FFFFFF;
    border: 1px solid #DDEAE6;
    border-radius: 13px;
    box-shadow: 0 5px 18px rgba(25,70,61,.045);
}

.statstrip .cell {
    padding: 14px 18px;
    border-left: 1px solid #E5EEEB;
    border-top: 3px solid var(--ac);
}

.statstrip .cell:first-child {
    border-left: none;
}

.statstrip .v {
    color: #21483F !important;
    font-family: "Plus Jakarta Sans", sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    line-height: 1.15;
}

.statstrip .l {
    color: #78918B !important;
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-top: 5px;
}

/* =========================================================
   OUTPUT CARDS
   ========================================================= */

.st-key-card_blog,
.st-key-card_linkedin,
.st-key-card_twitter,
.st-key-card_seo,
.st-key-card_factcheck,
.st-key-card_research {
    border-radius: 15px !important;
    padding: 25px 29px !important;
    font-size: .96rem !important;
    line-height: 1.78 !important;
    box-shadow: 0 6px 20px rgba(25,70,61,.045);
}

.st-key-card_blog {
    background: #F0FAF3;
    border: 1px solid #CFE7D5;
    border-left: 4px solid #4E9C6B;
}

.st-key-card_linkedin {
    background: #FFF5F5;
    border: 1px solid #F0D6D8;
    border-left: 4px solid #C66B72;
}

.st-key-card_twitter {
    background: #EEF8F6;
    border: 1px solid #CBE4DE;
    border-left: 4px solid #287A6E;
}

.st-key-card_seo {
    background: #FBF8ED;
    border: 1px solid #EAE0BD;
    border-left: 4px solid #B18C39;
}

.st-key-card_factcheck {
    background: #FFF6EE;
    border: 1px solid #F0D7C3;
    border-left: 4px solid #D67B42;
}

.st-key-card_research {
    background: #EEF9F7;
    border: 1px solid #CDE6E0;
    border-left: 4px solid #3A9183;
}

.st-key-card_blog *,
.st-key-card_linkedin *,
.st-key-card_twitter *,
.st-key-card_seo *,
.st-key-card_factcheck *,
.st-key-card_research * {
    font-family: "DM Sans", sans-serif;
}

.st-key-card_blog p,
.st-key-card_blog li,
.st-key-card_linkedin p,
.st-key-card_linkedin li,
.st-key-card_twitter p,
.st-key-card_twitter li,
.st-key-card_seo p,
.st-key-card_seo li,
.st-key-card_factcheck p,
.st-key-card_factcheck li,
.st-key-card_research p,
.st-key-card_research li {
    font-size: .96rem !important;
    line-height: 1.78 !important;
}

/* =========================================================
   RESEARCH / SOURCE BOXES
   ========================================================= */

.srcbox {
    background: #FFFFFF;
    border: 1px solid #DCEAE6;
    border-radius: 14px;
    padding: 17px 19px;
    margin-top: 13px;
}

.srcbox-title {
    color: #234F47 !important;
    font-family: "Plus Jakarta Sans", sans-serif;
    font-size: .86rem;
    font-weight: 800;
    margin-bottom: 11px;
}

.chiprow {
    display: flex;
    flex-wrap: wrap;
}

a.linkchip {
    display: inline-block;
    margin: 0 7px 7px 0;
    padding: 7px 12px;
    border-radius: 999px;
    background: #F3F8F6;
    border: 1px solid #D1E4DE;
    color: #2D655B !important;
    font-size: .76rem;
    font-weight: 700;
    text-decoration: none !important;
}

a.linkchip:hover {
    background: #E6F3EF;
    border-color: #9CCCBD;
}

ol.srclist {
    margin: 0;
    padding-left: 20px;
}

ol.srclist li {
    margin-bottom: 7px;
    color: #45675F !important;
    font-size: .82rem !important;
    line-height: 1.45 !important;
}

ol.srclist a {
    color: #176B5E !important;
    font-weight: 700;
    text-decoration: none;
}

ol.srclist a:hover {
    text-decoration: underline;
}

ol.srclist span {
    color: #8A9D98 !important;
    font-size: .72rem;
    margin-left: 7px;
}

/* =========================================================
   EXPANDERS / CODE
   ========================================================= */

[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #DCEAE6 !important;
    border-radius: 10px !important;
}

[data-testid="stExpander"] summary p {
    color: #315850 !important;
    font-size: .82rem !important;
    font-weight: 700 !important;
}

[data-testid="stCode"],
[data-testid="stCode"] pre {
    background: #F4F8F6 !important;
}

[data-testid="stCode"] code,
[data-testid="stCode"] span {
    color: #315850 !important;
}

/* =========================================================
   DOWNLOAD BUTTONS
   ========================================================= */

div.stDownloadButton > button {
    width: 100% !important;
    min-height: 2.55rem !important;
    border-radius: 9px !important;
    background: #F3F8F6 !important;
    border: 1px solid #CFE2DC !important;
    color: #28594F !important;
}

div.stDownloadButton > button:hover {
    background: #E8F3EF !important;
    border-color: #A8CEC2 !important;
}

div.stDownloadButton > button p {
    color: #28594F !important;
    font-size: .79rem !important;
    font-weight: 700 !important;
}

/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 900px) {

    .block-container {
        padding-top: 3rem !important;
    }

    .hero {
        padding: 32px 27px 28px;
        border-radius: 19px;
    }

    .hero .hero-title {
        font-size: 2.35rem !important;
    }

    .hero .hero-tag {
        font-size: 1rem !important;
    }

    .st-key-input_card {
        padding: 22px 20px 19px !important;
    }

    .st-key-chips [data-testid="stHorizontalBlock"] {
        grid-template-columns: repeat(2, minmax(0,1fr)) !important;
    }

    .st-key-chip_tools [data-testid="stHorizontalBlock"] {
        grid-template-columns: 1fr 1fr !important;
    }

    .st-key-chip_tools [data-testid="stColumn"]:nth-child(3) {
        grid-column: 1 / -1;
    }

    .st-key-chip_tools [data-testid="stColumn"]:nth-child(4) {
        display: none !important;
    }

    .st-key-chip_tools [data-testid="stColumn"]:nth-child(5) {
        grid-column: 1 / -1;
    }

    .statstrip {
        grid-template-columns: repeat(2, minmax(0,1fr));
    }

    .statstrip .cell:nth-child(3) {
        border-left: none;
        border-top: 1px solid #E5EEEB;
    }

    .statstrip .cell:nth-child(4) {
        border-top: 1px solid #E5EEEB;
    }

    .hero .feat span {
        border-left: none;
        padding: 4px 13px 4px 0;
    }
}

@media (max-width: 560px) {

    .hero .hero-title {
        font-size: 2rem !important;
    }

    .hero .feat {
        display: block;
    }

    .hero .feat span {
        display: block;
        padding: 4px 0;
    }

    .st-key-chips [data-testid="stHorizontalBlock"] {
        grid-template-columns: 1fr !important;
    }

    .statstrip .v {
        font-size: 1.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 9px !important;
    }

    .stTabs [data-baseweb="tab"] p {
        font-size: .72rem !important;
    }
}
"""
# ------------------------------------------------------------------ state
st.session_state.setdefault("history", [])
st.session_state.setdefault("result", None)
st.session_state.setdefault("topic", "")
for _k, _ in OUTPUTS:
    st.session_state.setdefault(f"sel_{_k}", False)


def get_api_key() -> str:
    """Key is read from Streamlit secrets or environment only - it is never shown in the UI."""
    try:
        v = st.secrets.get("GEMINI_API_KEY", "")
        if v:
            return v
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")


API_KEY = get_api_key()


def toggle(k: str):
    st.session_state[f"sel_{k}"] = not st.session_state[f"sel_{k}"]


def set_all(value: bool):
    for k, _ in OUTPUTS:
        st.session_state[f"sel_{k}"] = value


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="brand"><span class="logo">W</span><span class="bname"><span class="w3a">Writify</span> <span class="w3b">Studio</span></span></div><div class="brand-sub">Research. Write. Verify.</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="side-h">Model</div>', unsafe_allow_html=True)
    model_label = st.selectbox("AI model", list(MODELS.keys()), label_visibility="collapsed")

    st.markdown('<div class="side-h">Writing preferences</div>', unsafe_allow_html=True)
    language = st.selectbox("Output language", LANGUAGES)
    if language == CUSTOM_LANG:
        language = st.text_input("Type any language", placeholder="e.g. Arabic, Punjabi, Spanish, French").strip()
    if language == CUSTOM_LANG:
        language = st.text_input("Type any language", placeholder="e.g. French, Arabic, Punjabi, Spanish").strip() or "English"
    tone = st.selectbox("Tone of voice", TONES)
    length = st.selectbox("Blog length", list(LENGTHS.keys()), index=1)
    audience = st.text_input("Target audience", "Students and young professionals")

    st.markdown('<div class="side-h">Connection</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="status"><span class="dot {"ok" if API_KEY else "bad"}"></span>'
        f'{"Gemini connected" if API_KEY else "Not configured"}</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-h">Recent runs</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown('<div class="side-note">No runs yet.</div>', unsafe_allow_html=True)
    for i, h in enumerate(reversed(st.session_state.history[-6:])):
        if st.button(f"{h['time']}  |  {h['topic'][:26]}", key=f"hist_{i}"):
            st.session_state.result = h
            st.rerun()
    if st.session_state.history and st.button("Clear history", key="clear_hist"):
        st.session_state.history, st.session_state.result = [], None
        st.rerun()

# ------------------------------------------------------------------- hero
st.markdown(
    """
<div class="hero">
  <div class="eyebrow">&#9679; Multi-agent content studio</div>
  <div class="hero-title"><span class="w3a">Writify</span> <span class="w3b">Studio</span></div>
  <p class="hero-tag">One topic in. A fact-checked content package out.</p>
  <p>A crew of AI agents researches the web, writes the content, optimises it for search
  and verifies every claim, so you can publish with confidence.</p>
  <div class="feat"><span>Research report</span><span>Blog post</span><span>LinkedIn post</span><span>Twitter/X thread</span><span>SEO report</span><span>Fact-check</span></div>
</div>
""",
    unsafe_allow_html=True,
)

if not API_KEY:
    st.warning("The Gemini API key is not configured. Add GEMINI_API_KEY to your .env file or to the Streamlit "
               "secrets, then restart the app.")

# ------------------------------------------------------------------ input
EXAMPLES = ["AI agents in healthcare", "Remote work productivity", "Beginner's guide to investing"]

with st.container(key="input_card"):
    st.markdown('<div class="section-title">Topic</div>', unsafe_allow_html=True)
    st.text_area("Topic", key="topic", height=92, label_visibility="collapsed",
                 placeholder="Describe what you want to publish, e.g. How small businesses can use AI to save time")
    st.markdown('<div class="hint" style="margin:10px 0 6px">Try an example:</div>', unsafe_allow_html=True)
    with st.container(key="examples"):
        ex_cols = st.columns(len(EXAMPLES))
        for col, ex in zip(ex_cols, EXAMPLES):
            col.button(ex, key=f"ex_{ex}", on_click=lambda e=ex: st.session_state.update(topic=e))
    keywords = st.text_input("Focus keywords (optional)", placeholder="ai, automation, productivity")

    st.markdown('<div class="divider"></div><div class="section-title">Deliverables</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint-row"><span class="hint">Choose one or several outputs.</span>'
                '<span class="badge">Only selected outputs are delivered</span></div>', unsafe_allow_html=True)
    with st.container(key="chips"):
        cols = st.columns(len(OUTPUTS))
        for col, (k, label) in zip(cols, OUTPUTS):
            on = st.session_state[f"sel_{k}"]
            col.button(label, key=f"chip_{k}", type="primary" if on else "secondary",
                       on_click=toggle, args=(k,))
    selected = {k for k, _ in OUTPUTS if st.session_state.get(f"sel_{k}")}
    if "seo" in selected and "blog" not in selected:
        st.markdown('<div class="subnote">SEO editing works on a blog draft written in the background. The blog itself is shown only if you select Blog post.</div>',
                    unsafe_allow_html=True)
    with st.container(key="chip_tools"):
        b1, b2, b3, _sp, b5 = st.columns(5)
        b1.button("Select all", key="sel_all", on_click=set_all, args=(True,))
        b2.button("Clear", key="sel_none", on_click=set_all, args=(False,))
        b3.markdown(f'<div class="count">{len(selected)} of {len(OUTPUTS)} selected</div>', unsafe_allow_html=True)
        with b5:
            with st.container(key="go_wrap"):
                go = st.button("Generate content", type="primary", key="go", disabled=not API_KEY)


# --------------------------------------------------------------- pipeline
def pipeline_html(labels, done, active):
    h = '<div class="pipe">'
    for i, (_k, name) in enumerate(labels):
        cls = "done" if i < done else ("active" if i == active else "wait")
        state = "Completed" if i < done else ("In progress" if i == active else "Queued")
        h += f'<div class="step {cls}"><b>{name}</b>{state}</div>'
    return h + "</div>"


def visible_pipeline(steps, selected, n_done):
    """Show only the agents the user selected; background helpers (research / blog draft) stay hidden."""
    vis = [(i, st_) for i, st_ in enumerate(steps) if st_[0] in selected]
    labels = [v[1] for v in vis]
    done = sum(1 for i, _ in vis if i < n_done)
    active = next((j for j, (i, _) in enumerate(vis) if i >= n_done), -1)
    return pipeline_html(labels, done, active)


if go:
    topic = st.session_state.topic.strip()
    if len(topic) < 5:
        st.warning("Please describe the topic in a little more detail.")
    elif not language:
        st.warning("Please type the language you want in the sidebar (Output language > Custom language).")
    elif not selected:
        st.warning("Select at least one deliverable.")
    else:
        all_steps = plan_steps(selected)
        # a blog drafted only for SEO is a background step: it runs but is not shown
        steps = [st_ for st_ in all_steps if st_[0] != "blog" or "blog" in selected]
        holder = st.empty()
        state = {"raw": 0, "done": 0}
        holder.markdown(pipeline_html(steps, 0, 0), unsafe_allow_html=True)

        def on_done(_o):
            key = all_steps[state["raw"]][0] if state["raw"] < len(all_steps) else None
            state["raw"] += 1
            if key != "blog" or "blog" in selected:
                state["done"] += 1
            holder.markdown(pipeline_html(steps, state["done"], state["done"]), unsafe_allow_html=True)

        cfg = dict(topic=topic, audience=audience, tone=tone, language=language, length=length,
                   keywords=keywords, outputs=selected)
        start = time.time()
        try:
            with st.spinner("The agents are working. This can take a few minutes on the free tier."):
                order = [MODELS[model_label]] + [m for m in MODELS.values() if m != MODELS[model_label]]
                out = None
                for n, mdl in enumerate(order):
                    state["done"] = 0
                    state["raw"] = 0
                    holder.markdown(visible_pipeline(steps, selected, 0), unsafe_allow_html=True)
                    try:
                        out = run_studio(cfg, mdl, API_KEY, on_done)
                        break
                    except Exception as e:  # noqa: BLE001
                        retry = any(x in str(e) for x in ("503", "UNAVAILABLE", "high demand", "429", "404", "NOT_FOUND"))
                        if retry and n < len(order) - 1:
                            st.toast("Model unavailable or busy. Trying the next model.")
                            time.sleep(8)
                            continue
                        raise
            out.update(topic=topic, time=dt.datetime.now().strftime("%H:%M"),
                       seconds=int(time.time() - start), agents=len(all_steps), keywords=keywords)
            st.session_state.result = out
            st.session_state.history.append(out)
            holder.markdown(visible_pipeline(steps, selected, len(steps)), unsafe_allow_html=True)
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg:
                st.error("Gemini servers are busy right now. Please wait a minute or two and try again.")
            elif "404" in msg or "NOT_FOUND" in msg:
                st.error("This model is no longer available. Update the MODELS list in crew_setup.py.")
            elif "429" in msg or "quota" in msg.lower() or "rate limit" in msg.lower():
                st.error("The Gemini free-tier limit was reached. Wait a minute, or choose a Flash-Lite model.")
            elif "API key" in msg or "401" in msg or "403" in msg or "invalid" in msg.lower():
                st.error("The configured API key was rejected. Check the key in your .env file or secrets.")
            else:
                st.error("Something went wrong. Please try again.")
            with st.expander("Technical details"):
                st.code(msg)


# ------------------------------------------------------- research extras
def google_links(topic: str, keywords: str):
    year = dt.date.today().year
    g = "https://www.google.com/search?q="
    links = [
        ("Overview", g + quote_plus(topic)),
        ("Statistics and data", g + quote_plus(f"{topic} statistics")),
        (f"Trends {year}", g + quote_plus(f"{topic} trends {year}")),
        ("Latest news", "https://www.google.com/search?tbm=nws&q=" + quote_plus(topic)),
        ("Research papers", "https://scholar.google.com/scholar?q=" + quote_plus(topic)),
    ]
    for kw in [k.strip() for k in (keywords or "").split(",") if k.strip()][:3]:
        links.append((f"Keyword: {kw}", g + quote_plus(f"{topic} {kw}")))
    return links


def research_extras(res: dict):
    chips = "".join(
        f'<a class="linkchip" href="{html.escape(u, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(t)}</a>'
        for t, u in google_links(res["topic"], res.get("keywords", "")))
    st.markdown(f'<div class="srcbox"><div class="srcbox-title">Explore this topic on Google</div>'
                f'<div class="chiprow">{chips}</div></div>', unsafe_allow_html=True)
    srcs = res.get("sources") or []
    if srcs:
        items = ""
        for sc in srcs[:15]:
            dom = urlparse(sc["url"]).netloc.replace("www.", "")
            items += (f'<li><a href="{html.escape(sc["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
                      f'{html.escape(sc["title"][:110])}</a><span>{html.escape(dom)}</span></li>')
        body = f'<ol class="srclist">{items}</ol>'
    else:
        body = '<div class="hint">No live sources were captured for this run.</div>'
    st.markdown(f'<div class="srcbox"><div class="srcbox-title">Sources used by the research agent</div>{body}</div>',
                unsafe_allow_html=True)


def export_text(res: dict, key: str) -> str:
    text = res[key]
    if key == "research" and res.get("sources"):
        text += "\n\n## Sources\n" + "\n".join(f"- [{x['title']}]({x['url']})" for x in res["sources"])
    return text


def stat_strip(label: str, key: str, res: dict):
    """Four stats computed from the text of THIS tab only."""
    text = res[key]
    words = len(text.split())
    chars = len(text)
    mins = max(1, round(words / 200))
    if key == "blog":
        extra = (str(len(re.findall(r"^#{1,6}\s", text, re.M))), "Headings")
    elif key == "linkedin":
        extra = (str(len(re.findall(r"(?<!\w)#\w+", text))), "Hashtags")
    elif key == "twitter":
        extra = (str(len(re.findall(r"^\s*\**\d+\s*/", text, re.M))), "Tweets")
    elif key == "factcheck":
        m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
        extra = (f"{m.group(1)}/10" if m else "-", "Reliability score")
    elif key == "research":
        extra = (str(len(res.get("sources") or [])), "Sources found")
    else:  # seo
        extra = (str(len(re.findall(r"^\s*(?:[-*]|\d+\.)\s", text, re.M))), "Checklist items")
    cells = [(f"{words:,}", "Words"), (f"{chars:,}", "Characters"), (f"{mins} min", "Reading time"), extra]
    ac = THEMES[key]["ac"]
    inner = "".join(f'<div class="cell"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in cells)
    st.markdown(f'<div class="statstrip" style="--ac:{ac}">{inner}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- results
res = st.session_state.result
if res:
    st.markdown(f'<div class="result-head">Results <span>{html.escape(res["topic"])}</span></div>',
                unsafe_allow_html=True)
    TAB_ORDER = [("Blog", "blog"), ("LinkedIn", "linkedin"), ("Twitter/X", "twitter"),
                 ("SEO", "seo"), ("Fact-check", "factcheck"), ("Research", "research")]
    sections = [(lbl, k) for lbl, k in TAB_ORDER if res.get(k)]

    st.markdown(
        f'<div class="runbar"><span><b>{len(sections)}</b> deliverable{"s" if len(sections) != 1 else ""}</span>'
        f'<span><b>{res["agents"]}</b> agents run</span><span><b>{res["seconds"]}s</b> total time</span></div>',
        unsafe_allow_html=True)

    tabs = st.tabs([s[0] for s in sections]) if sections else []
    for tab, (label, key) in zip(tabs, sections):
        with tab:
            stat_strip(label, key, res)
            with st.container(key=f"card_{key}"):
                st.markdown(res[key])
            if key == "research":
                research_extras(res)
            c1, c2 = st.columns([1, 3])
            c1.download_button("Download (.md)", export_text(res, key), file_name=f"{key}.md", key=f"dl_{key}")
            with st.expander("Copy raw text"):
                st.code(export_text(res, key), language=None)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for _lbl, key in sections:
            z.writestr(f"{key}.md", export_text(res, key))
    st.download_button("Download full package (.zip)", buf.getvalue(), file_name="content_package.zip",
                       mime="application/zip", type="primary", key="dl_zip")
else:
    st.markdown('<div class="note">Enter a topic, choose your deliverables and select Generate content.</div>', unsafe_allow_html=True)
