"""CyberTrace About & Limitations page."""

import streamlit as st
from app.db.connection import using_hosted_database
from app.ui.components import footer


def render():
    st.markdown("## ℹ️ About & Limitations")

    st.markdown("""
### What CyberTrace Is

CyberTrace is an educational **digital footprint privacy assessment tool**. It helps
you reflect on what personal information you've chosen to share publicly, estimates
a risk score from your own answers using a transparent weighted formula, and gives
you personalized, actionable recommendations.
""")

    st.markdown("""
### What CyberTrace Is NOT

CyberTrace does **not**:
- Search data-breach databases or confirm whether your email/password has been breached.
- Monitor the dark web.
- Operate as an internet-wide people-search engine.
- Scrape, log into, or automatically inspect your social media accounts.
- Predict identity theft or guarantee your safety.
- Fetch or verify any URL you provide — URLs are validated only for format.
""")

    st.markdown("""
### A, B, and C: Understanding Your Results

Every piece of information in this app falls into one of three categories:

- **A — Information you supplied.** Your answers to the assessment questions.
- **B — Risk inferred from that information.** The scores and recommendations
  CyberTrace calculates based on what you told it.
- **C — Independently verified information.** CyberTrace does **not** currently
  perform this kind of verification. Nothing in this app should be read as a
  confirmed, externally verified finding about you.
""")

    st.markdown("### How Scoring Works")
    with st.expander("Full scoring methodology"):
        st.markdown("""
Each applicable question contributes a risk value between 0 (no risk) and 1
(maximum risk), multiplied by that question's weight. All weighted values are
summed and divided by the total applicable weight, then multiplied by 100:

```
Risk Score = 100 × Σ(risk_value × weight) / Σ(applicable weights)
```

- **0–24: LOW**
- **25–49: MODERATE**
- **50–74: HIGH**
- **75–100: CRITICAL**

Questions answered "Not applicable" are excluded from both the numerator and
denominator of this formula — they are never treated as safe or risky.
Protective-practice questions (e.g. "Do you use MFA?") use a reversed scale,
so answering that you *do* follow the protective practice lowers your risk value.
""")

    st.markdown("### Data Handling")
    hosted = using_hosted_database()
    if hosted:
        st.markdown("""
<div class="ct-notice">
This deployment is configured to use a hosted database. Your assessment history
is expected to persist across sessions.
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="ct-warning">
<strong>Storage notice:</strong> This deployment is currently using local SQLite
storage. On Streamlit Community Cloud, local storage is <strong>not guaranteed to
persist</strong> — it may be reset on redeploys, restarts, or sleep/wake cycles.
Do not rely on this instance for long-term storage unless a hosted database has
been configured by the administrator.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
We do not require passwords for any third-party service, do not scrape private
accounts, and do not collect more personal information than necessary for the
features you choose to use. Account passwords are hashed with bcrypt and never
stored in plaintext. You can delete your account and all associated data at any
time from your profile settings.
""")

    st.markdown("### Source & Feedback")
    st.markdown("""
CyberTrace is built entirely with Python and Streamlit — no proprietary AI
services or paid APIs are required for any core feature. If you notice an issue
or have feedback, please contact the maintainer of this deployment.
""")

    st.markdown("---")
    footer()
