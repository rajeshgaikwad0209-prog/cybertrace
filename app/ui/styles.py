"""CyberTrace custom CSS — dark navy/charcoal theme with cyan accents."""

import streamlit as st

CUSTOM_CSS = """
<style>
:root {
    --ct-navy: #0B1C2C;
    --ct-navy-light: #132A3F;
    --ct-charcoal: #11161C;
    --ct-cyan: #17A2B8;
    --ct-cyan-bright: #2FD3E8;
    --ct-teal: #0E7C7B;
    --ct-text: #E8EEF3;
    --ct-text-muted: #9FB3C4;
    --ct-low: #2ecc71;
    --ct-moderate: #f1c40f;
    --ct-high: #e67e22;
    --ct-critical: #e74c3c;
    --ct-border: #22384A;
}

/* App background */
.stApp {
    background: linear-gradient(180deg, var(--ct-navy) 0%, var(--ct-charcoal) 100%);
}

/* Headings */
h1, h2, h3 {
    color: var(--ct-text) !important;
    font-weight: 700 !important;
}

h1 { letter-spacing: -0.5px; }

p, li, label, span {
    color: var(--ct-text);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--ct-navy-light);
    border-right: 1px solid var(--ct-border);
}

/* Cards */
.ct-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--ct-border);
    border-radius: 12px;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
}

.ct-card h3, .ct-card h4 {
    margin-top: 0;
}

.ct-hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem 1rem;
}

.ct-hero-badge {
    display: inline-block;
    background: rgba(23,162,184,0.15);
    color: var(--ct-cyan-bright);
    border: 1px solid var(--ct-cyan);
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
}

.ct-logo-text {
    font-size: 2.6rem;
    font-weight: 800;
    color: var(--ct-text);
    letter-spacing: -1px;
}
.ct-logo-text span { color: var(--ct-cyan-bright); }

.ct-tagline {
    color: var(--ct-text-muted);
    font-size: 1.1rem;
    margin-top: 0.3rem;
}

/* Feature cards grid */
.ct-feature-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--ct-border);
    border-radius: 12px;
    padding: 1.2rem;
    height: 100%;
    transition: border-color 0.15s ease;
}
.ct-feature-card:hover {
    border-color: var(--ct-cyan);
}
.ct-feature-icon {
    font-size: 1.6rem;
    margin-bottom: 0.4rem;
}

/* Risk badges */
.ct-badge {
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.3px;
}
.ct-badge-low { background: rgba(46,204,113,0.15); color: var(--ct-low); border: 1px solid var(--ct-low); }
.ct-badge-moderate { background: rgba(241,196,15,0.15); color: var(--ct-moderate); border: 1px solid var(--ct-moderate); }
.ct-badge-high { background: rgba(230,126,34,0.15); color: var(--ct-high); border: 1px solid var(--ct-high); }
.ct-badge-critical { background: rgba(231,76,60,0.15); color: var(--ct-critical); border: 1px solid var(--ct-critical); }

/* Score circle */
.ct-score-display {
    text-align: center;
    padding: 1.5rem;
}
.ct-score-number {
    font-size: 4rem;
    font-weight: 800;
    line-height: 1;
}
.ct-score-label {
    color: var(--ct-text-muted);
    font-size: 0.95rem;
    margin-top: 0.3rem;
}

/* Notice / warning boxes */
.ct-notice {
    background: rgba(23,162,184,0.08);
    border-left: 3px solid var(--ct-cyan);
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.92rem;
    color: var(--ct-text-muted);
}

.ct-warning {
    background: rgba(230,126,34,0.08);
    border-left: 3px solid var(--ct-high);
    border-radius: 6px;
    padding: 0.9rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.92rem;
    color: var(--ct-text-muted);
}

/* Footer */
.ct-footer {
    text-align: center;
    color: var(--ct-text-muted);
    font-size: 0.85rem;
    padding: 2rem 1rem 1rem 1rem;
    border-top: 1px solid var(--ct-border);
    margin-top: 2rem;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    border: 1px solid var(--ct-cyan);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--ct-cyan) 0%, var(--ct-teal) 100%);
    border: none;
}

/* Progress bar accent */
.stProgress > div > div > div > div {
    background-image: linear-gradient(90deg, var(--ct-cyan) 0%, var(--ct-cyan-bright) 100%);
}

/* Metric styling */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--ct-border);
    border-radius: 10px;
    padding: 0.8rem;
}

/* Divider spacing */
hr { border-color: var(--ct-border) !important; }
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def risk_badge_html(level: str) -> str:
    css_class = {
        "LOW": "ct-badge-low",
        "MODERATE": "ct-badge-moderate",
        "HIGH": "ct-badge-high",
        "CRITICAL": "ct-badge-critical",
    }.get(level, "ct-badge-low")
    return f'<span class="ct-badge {css_class}">{level}</span>'
