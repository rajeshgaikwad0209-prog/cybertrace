"""Reusable Streamlit UI component helpers for CyberTrace."""

import html
import streamlit as st
from app.ui.styles import risk_badge_html
from app.core.scoring import ScoringResult


def render_score_display(result: ScoringResult):
    if result.overall_score is None:
        st.markdown(
            '<div class="ct-notice">No score available yet. Complete an assessment to see your results.</div>',
            unsafe_allow_html=True
        )
        return

    color_map = {"LOW": "#2ecc71", "MODERATE": "#f1c40f", "HIGH": "#e67e22", "CRITICAL": "#e74c3c"}
    color = color_map.get(result.overall_risk_level, "#888")
    st.markdown(f"""
    <div class="ct-score-display">
        <div class="ct-score-number" style="color:{color};">{result.overall_score:.1f}</div>
        <div class="ct-score-label">out of 100</div>
        <div style="margin-top:0.6rem;">{risk_badge_html(result.overall_risk_level)}</div>
    </div>
    """, unsafe_allow_html=True)


def render_category_cards(result: ScoringResult):
    from app.core.questions import CATEGORY_ORDER, CATEGORIES, CATEGORY_DESCRIPTIONS
    cols = st.columns(3)
    for i, cat_key in enumerate(CATEGORY_ORDER):
        cs = result.category_scores.get(cat_key)
        with cols[i % 3]:
            if cs is None or cs.score is None:
                st.markdown(f"""
                <div class="ct-card">
                    <h4>{CATEGORIES[cat_key]}</h4>
                    <p style="color:#9FB3C4; font-size:0.85rem;">{CATEGORY_DESCRIPTIONS[cat_key]}</p>
                    <p style="color:#9FB3C4;">No applicable answers</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ct-card">
                    <h4>{CATEGORIES[cat_key]}</h4>
                    <p style="color:#9FB3C4; font-size:0.85rem;">{CATEGORY_DESCRIPTIONS[cat_key]}</p>
                    <div style="font-size:1.8rem; font-weight:700; margin:0.2rem 0;">{cs.score:.1f}</div>
                    {risk_badge_html(cs.risk_level)}
                    <p style="color:#9FB3C4; font-size:0.8rem; margin-top:0.5rem;">
                        {cs.applicable_count} applicable &bull; {cs.concern_count} concern(s)
                    </p>
                </div>
                """, unsafe_allow_html=True)


def render_feature_card(icon: str, title: str, description: str):
    st.markdown(f"""
    <div class="ct-feature-card">
        <div class="ct-feature-icon">{icon}</div>
        <h4 style="margin-bottom:0.3rem;">{html.escape(title)}</h4>
        <p style="color:#9FB3C4; font-size:0.88rem; margin:0;">{html.escape(description)}</p>
    </div>
    """, unsafe_allow_html=True)


def render_recommendation_card(rec, completed: bool, on_toggle_key: str):
    priority_colors = {"Critical": "#e74c3c", "High": "#e67e22", "Medium": "#f1c40f", "Low": "#2ecc71"}
    color = priority_colors.get(rec.priority, "#888")
    strike = "text-decoration:line-through; opacity:0.6;" if completed else ""
    st.markdown(f"""
    <div class="ct-card" style="{strike} border-left: 3px solid {color};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">{html.escape(rec.title)}</h4>
            <span style="color:{color}; font-weight:700; font-size:0.8rem;">{rec.priority.upper()}</span>
        </div>
        <p style="color:#9FB3C4; font-size:0.88rem; margin-top:0.4rem;">{html.escape(rec.explanation)}</p>
        <p style="color:#9FB3C4; font-size:0.78rem; font-style:italic;">Why: {html.escape(rec.reason)}</p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Action steps"):
        for step in rec.action_steps:
            st.markdown(f"- {step}")
    st.checkbox("Mark as completed", value=completed, key=on_toggle_key)


def privacy_notice():
    st.markdown("""
    <div class="ct-notice">
    <strong>How we handle your data:</strong> CyberTrace evaluates information you choose
    to provide. We do not scrape social media, search data-breach databases, or verify
    anything independently. Your answers are stored only to let you track progress over
    time; you can delete your account and all data at any time from your profile settings.
    </div>
    """, unsafe_allow_html=True)


def limitations_notice():
    st.markdown("""
    <div class="ct-warning">
    <strong>Limitations:</strong> This is an educational self-assessment based on
    information you supply. It does not discover data breaches, dark-web exposure, or
    public records automatically, and it is not a guarantee of safety or a validated
    prediction of identity theft risk.
    </div>
    """, unsafe_allow_html=True)


def footer():
    st.markdown("""
    <div class="ct-footer">
        <strong>CyberTrace</strong> — Digital Footprint &amp; Privacy Risk Analyzer<br>
        Educational privacy assessment tool. Not a substitute for professional security advice.<br>
        See "About &amp; Limitations" for full details on what this tool does and does not do.
    </div>
    """, unsafe_allow_html=True)
