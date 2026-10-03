"""Lumen Studio - multi-agent content intelligence (CrewAI + Gemini + DuckDuckGo + Streamlit)."""
import html
import io
import os
import sys
import time
import zipfile
import datetime as dt

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

from crew_setup import (LANGUAGES, LENGTHS, MODELS, OUTPUTS, TONES,  # noqa: E402
                        plan_steps, resolve_outputs, run_studio)

st.set_page_config(page_title="Lumen Studio", page_icon=":material/auto_awesome:", layout="wide")

# ------------------------------------------------------------------ theme
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

.stApp {background: linear-gradient(160deg,#EEF1FB 0%,#F6F3FF 48%,#E9F5F7 100%);}
.stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button, .stApp td, .stApp th {font-family:'Manrope',sans-serif;}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {font-family:'Sora',sans-serif; letter-spacing:-.01em;}
#MainMenu, footer {visibility:hidden;}
.block-container {padding-top:1.4rem; max-width:1180px;}

/* sidebar */
section[data-testid="stSidebar"] {background: linear-gradient(185deg,#0C1230 0%,#1B1A5E 55%,#0E5A73 135%) !important;}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {background: transparent !important;}
.brand {font-family:'Sora',sans-serif; font-size:1.55rem; font-weight:800; color:#FFFFFF; letter-spacing:-.02em; margin-top:4px;}
.brand-sub {color:#A9B4FF; font-size:.82rem; margin-bottom:18px; letter-spacing:.04em; text-transform:uppercase;}
.side-h {color:#8FA0FF; font-size:.72rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin:20px 0 6px;}
.status {display:flex; align-items:center; gap:8px; font-size:.85rem; color:#DDE3FF; margin-top:6px;}
.dot {width:9px; height:9px; border-radius:50%; display:inline-block;}
.dot.ok {background:#34D399; box-shadow:0 0 0 4px rgba(52,211,153,.2);} .dot.bad {background:#F87171;}
section[data-testid="stSidebar"] button {width:100%; background:rgba(255,255,255,.08) !important; border:1px solid rgba(255,255,255,.2) !important;}
section[data-testid="stSidebar"] button p {color:#E6E9FF !important; font-size:.85rem;}

/* hero */
.hero {position:relative; overflow:hidden; border-radius:22px; padding:38px 42px; margin-bottom:22px;
  background: radial-gradient(900px 300px at 85% -10%, rgba(34,211,238,.35), transparent 60%),
              linear-gradient(120deg,#0B1030 0%,#2A1B7A 52%,#0E7490 100%);
  box-shadow:0 18px 40px rgba(27,26,94,.28);}
.hero .eyebrow {color:#9FB0FF; font-size:.78rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase;}
.hero h1 {color:#FFFFFF !important; font-size:2.6rem; font-weight:800; margin:6px 0 8px; padding:0;}
.hero p {color:#DCE3FF !important; font-size:1.02rem; max-width:720px; margin:0; line-height:1.6;}
.hero .chips span {display:inline-block; margin:18px 8px 0 0; padding:5px 13px; border-radius:999px; font-size:.78rem;
  color:#F1F4FF; background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22);}

/* input card */
.st-key-input_card {background:#FFFFFF; border:1px solid #E3E7F5; border-radius:18px; padding:22px 26px 18px;
  box-shadow:0 6px 24px rgba(30,40,90,.07);}
.section-title {font-family:'Sora',sans-serif; font-weight:700; font-size:1.02rem; color:#1B2033; margin:2px 0 8px;}
.hint {color:#5B6477; font-size:.85rem;}
.stButton > button, .stDownloadButton > button {width:100%; border-radius:11px; font-weight:600;}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background:linear-gradient(120deg,#4F46E5,#0891B2) !important; color:#FFFFFF !important; border:none !important;
  padding:.7rem 1rem; font-size:1rem; box-shadow:0 8px 20px rgba(79,70,229,.3);}
button[data-testid="stBaseButton-primary"] p {color:#FFFFFF !important;}

/* pipeline */
.pipe {display:flex; gap:10px; flex-wrap:wrap; margin:14px 0 8px;}
.step {flex:1; min-width:150px; background:#FFFFFF; border:1px solid #E3E7F5; border-radius:14px; padding:12px 15px; color:#1B2033; font-size:.85rem;}
.step b {display:block; font-family:'Sora',sans-serif; font-size:.88rem; margin-bottom:2px; color:#1B2033;}
.step.done {border-color:#10B981; background:#ECFDF5; color:#065F46;} .step.done b {color:#065F46;}
.step.active {border-color:#4F46E5; background:#EEF2FF; color:#3730A3; animation:pulse 1.4s infinite;} .step.active b {color:#3730A3;}
.step.wait {opacity:.6;}
@keyframes pulse {0%{box-shadow:0 0 0 0 rgba(79,70,229,.35)} 100%{box-shadow:0 0 0 12px rgba(79,70,229,0)}}

/* results */
.result-head {font-family:'Sora',sans-serif; font-size:1.35rem; font-weight:700; color:#1B2033; margin:26px 0 2px;}
.result-head span {color:#4F46E5;}
.metric {background:#FFFFFF; border:1px solid #E3E7F5; border-radius:14px; padding:14px 16px;}
.metric .v {font-family:'Sora',sans-serif; font-size:1.55rem; font-weight:800; color:#4F46E5;}
.metric .l {font-size:.72rem; color:#5B6477; text-transform:uppercase; letter-spacing:.08em;}
.stTabs [data-baseweb="tab-list"] {gap:6px;}
.stTabs [data-baseweb="tab"] {background:#FFFFFF; border-radius:10px 10px 0 0; padding:9px 18px;}
"""

# each output gets its own colour theme: bg / text / accent (all with strong contrast)
THEMES = {
    "blog":      dict(bg="#EEF2FF", fg="#1E1B4B", ac="#4338CA"),
    "linkedin":  dict(bg="#E8F2FC", fg="#0A2540", ac="#0A66C2"),
    "twitter":   dict(bg="#0F172A", fg="#E2E8F0", ac="#38BDF8"),
    "seo":       dict(bg="#ECFDF5", fg="#053D2E", ac="#047857"),
    "factcheck": dict(bg="#FFF4E8", fg="#5A2509", ac="#C2410C"),
    "research":  dict(bg="#F1F5F9", fg="#0F172A", ac="#475569"),
}


def theme_css() -> str:
    css = ""
    for k, t in THEMES.items():
        s = f".st-key-card_{k}"
        css += (
            f"{s}{{background:{t['bg']};border:1px solid {t['ac']}44;border-left:6px solid {t['ac']};"
            f"border-radius:16px;padding:22px 28px;}}"
            f"{s} p,{s} li,{s} td,{s} th,{s} span,{s} blockquote,{s} strong,{s} em{{color:{t['fg']} !important;}}"
            f"{s} h1,{s} h2,{s} h3,{s} h4,{s} a{{color:{t['ac']} !important;}}"
        )
    return css


st.markdown(f"<style>{BASE_CSS}{theme_css()}</style>", unsafe_allow_html=True)

# ------------------------------------------------------------------ state
st.session_state.setdefault("history", [])
st.session_state.setdefault("result", None)
st.session_state.setdefault("topic", "")
for _k, _ in OUTPUTS:
    st.session_state.setdefault(f"sel_{_k}", True)


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


def set_all(value: bool):
    for k, _ in OUTPUTS:
        st.session_state[f"sel_{k}"] = value


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="brand">Lumen Studio</div><div class="brand-sub">Content intelligence</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="side-h">Model</div>', unsafe_allow_html=True)
    model_label = st.selectbox("AI model", list(MODELS.keys()), label_visibility="collapsed")

    st.markdown('<div class="side-h">Writing preferences</div>', unsafe_allow_html=True)
    language = st.selectbox("Output language", LANGUAGES)
    tone = st.selectbox("Tone of voice", TONES)
    length = st.selectbox("Blog length", list(LENGTHS.keys()), index=1)
    audience = st.text_input("Target audience", "Students and young professionals")

    st.markdown('<div class="side-h">Connection</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="status"><span class="dot {"ok" if API_KEY else "bad"}"></span>'
        f'{"Gemini connected" if API_KEY else "Not configured"}</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-h">Recent runs</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.caption("No runs yet.")
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
  <div class="eyebrow">Multi-agent content intelligence</div>
  <h1>Lumen Studio</h1>
  <p>Turn a single topic into research-backed articles, social content and SEO assets,
  produced and fact-checked by a team of specialised AI agents.</p>
  <div class="chips"><span>Researcher</span><span>Blog Writer</span><span>LinkedIn Writer</span>
  <span>Twitter/X Writer</span><span>SEO Editor</span><span>Fact-Checker</span></div>
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
    ex_cols = st.columns(len(EXAMPLES))
    for col, ex in zip(ex_cols, EXAMPLES):
        col.button(ex, key=f"ex_{ex}", on_click=lambda e=ex: st.session_state.update(topic=e))
    keywords = st.text_input("Focus keywords (optional)", placeholder="ai, automation, productivity")

    st.markdown('<div class="section-title" style="margin-top:14px">Deliverables</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint">Choose a single deliverable or any combination. Research always runs first.</div>',
                unsafe_allow_html=True)
    cols = st.columns(len(OUTPUTS))
    for col, (k, label) in zip(cols, OUTPUTS):
        col.checkbox(label, key=f"sel_{k}")
    b1, b2, _sp = st.columns([1, 1, 4])
    b1.button("Select all", key="sel_all", on_click=set_all, args=(True,))
    b2.button("Clear", key="sel_none", on_click=set_all, args=(False,))

    selected = {k for k, _ in OUTPUTS if st.session_state.get(f"sel_{k}")}
    if "seo" in selected and "blog" not in selected:
        st.caption("SEO editing needs a blog draft, so the Blog Writer will run automatically.")
    st.write("")
    go = st.button("Generate content", type="primary", key="go", disabled=not API_KEY)


# --------------------------------------------------------------- pipeline
def pipeline_html(labels, done, active):
    h = '<div class="pipe">'
    for i, (_k, name) in enumerate(labels):
        cls = "done" if i < done else ("active" if i == active else "wait")
        state = "Completed" if i < done else ("In progress" if i == active else "Queued")
        h += f'<div class="step {cls}"><b>{name}</b>{state}</div>'
    return h + "</div>"


if go:
    topic = st.session_state.topic.strip()
    content_sel = selected & {"blog", "linkedin", "twitter", "seo"}
    if len(topic) < 5:
        st.warning("Please describe the topic in a little more detail.")
    elif not content_sel:
        st.warning("Select at least one content type (blog, LinkedIn, Twitter/X or SEO).")
    else:
        steps = plan_steps(selected)
        holder = st.empty()
        state = {"done": 0}
        holder.markdown(pipeline_html(steps, 0, 0), unsafe_allow_html=True)

        def on_done(_o):
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
                    holder.markdown(pipeline_html(steps, 0, 0), unsafe_allow_html=True)
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
                       seconds=int(time.time() - start), agents=len(steps))
            st.session_state.result = out
            st.session_state.history.append(out)
            holder.markdown(pipeline_html(steps, len(steps), -1), unsafe_allow_html=True)
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

# ---------------------------------------------------------------- results
res = st.session_state.result
if res:
    st.markdown(f'<div class="result-head">Results <span>{html.escape(res["topic"])}</span></div>',
                unsafe_allow_html=True)
    TAB_ORDER = [("Blog", "blog"), ("LinkedIn", "linkedin"), ("Twitter/X", "twitter"),
                 ("SEO", "seo"), ("Fact-check", "factcheck"), ("Research", "research")]
    sections = [(lbl, k) for lbl, k in TAB_ORDER if res.get(k)]

    stats = [(f"{len(res['blog'].split()):,}" if res.get("blog") else "-", "Blog words"),
             (res["agents"], "Agents run"), (len(sections), "Deliverables"), (f"{res['seconds']}s", "Total time")]
    for col, (v, l) in zip(st.columns(4), stats):
        col.markdown(f'<div class="metric"><div class="v">{v}</div><div class="l">{l}</div></div>',
                     unsafe_allow_html=True)
    st.write("")

    tabs = st.tabs([s[0] for s in sections])
    for tab, (label, key) in zip(tabs, sections):
        with tab:
            with st.container(key=f"card_{key}"):
                st.markdown(res[key])
            c1, c2 = st.columns([1, 3])
            c1.download_button("Download (.md)", res[key], file_name=f"{key}.md", key=f"dl_{key}")
            with st.expander("Copy raw text"):
                st.code(res[key], language="markdown")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for _lbl, key in sections:
            z.writestr(f"{key}.md", res[key])
    st.download_button("Download full package (.zip)", buf.getvalue(), file_name="content_package.zip",
                       mime="application/zip", type="primary", key="dl_zip")
else:
    st.info("Enter a topic, choose your deliverables and select Generate content.")
