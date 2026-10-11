"""Reusable Plotly chart builders for CyberTrace."""

import plotly.graph_objects as go
from app.core.scoring import ScoringResult, RISK_LEVEL_COLORS
from app.core.questions import CATEGORY_ORDER, CATEGORIES

PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG = "rgba(0,0,0,0)"
FONT_COLOR = "#E8EEF3"
GRID_COLOR = "#22384A"


def _base_layout(title: str = "", height: int = 400) -> dict:
    return dict(
        title=dict(text=title, font=dict(color=FONT_COLOR, size=16)),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        height=height,
        margin=dict(l=40, r=30, t=50, b=40),
    )


def category_bar_chart(result: ScoringResult) -> go.Figure:
    labels, scores, colors_ = [], [], []
    for cat_key in CATEGORY_ORDER:
        cs = result.category_scores.get(cat_key)
        labels.append(CATEGORIES[cat_key])
        score = cs.score if cs and cs.score is not None else 0
        scores.append(score)
        level = cs.risk_level if cs and cs.risk_level else "LOW"
        colors_.append(RISK_LEVEL_COLORS.get(level, "#888888"))

    fig = go.Figure(go.Bar(
        x=scores, y=labels, orientation="h",
        marker=dict(color=colors_),
        text=[f"{s:.1f}" if s else "N/A" for s in scores],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
    ))
    fig.update_layout(**_base_layout("Risk Score by Category", height=380))
    fig.update_xaxes(range=[0, 105], gridcolor=GRID_COLOR, title="Risk Score (0-100)")
    fig.update_yaxes(gridcolor=GRID_COLOR, autorange="reversed")
    return fig


def exposure_radar_chart(result: ScoringResult) -> go.Figure:
    labels, scores = [], []
    for cat_key in CATEGORY_ORDER:
        cs = result.category_scores.get(cat_key)
        labels.append(CATEGORIES[cat_key])
        scores.append(cs.score if cs and cs.score is not None else 0)

    # Close the loop for radar
    labels_closed = labels + [labels[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed, theta=labels_closed, fill="toself",
        fillcolor="rgba(23,162,184,0.25)",
        line=dict(color="#2FD3E8", width=2),
        name="Risk Exposure",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=PLOT_BG,
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=GRID_COLOR, color=FONT_COLOR),
            angularaxis=dict(gridcolor=GRID_COLOR, color=FONT_COLOR),
        ),
        showlegend=False,
        **_base_layout("Digital Exposure Map", height=450),
    )
    return fig


def risk_level_summary_chart(result: ScoringResult) -> go.Figure:
    from collections import Counter
    levels = [cs.risk_level for cs in result.category_scores.values() if cs.risk_level]
    counts = Counter(levels)
    order = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    x = [lvl for lvl in order if counts.get(lvl, 0) > 0]
    y = [counts.get(lvl, 0) for lvl in x]
    colors_ = [RISK_LEVEL_COLORS[lvl] for lvl in x]

    fig = go.Figure(go.Bar(
        x=x, y=y, marker=dict(color=colors_),
        text=y, textposition="outside",
    ))
    fig.update_layout(**_base_layout("Categories by Risk Level", height=320))
    fig.update_xaxes(gridcolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, title="Number of Categories", dtick=1)
    return fig


def history_trend_chart(dates, scores) -> go.Figure:
    colors_ = []
    from app.core.scoring import risk_level
    for s in scores:
        lvl = risk_level(s)
        colors_.append(RISK_LEVEL_COLORS[lvl])

    fig = go.Figure(go.Scatter(
        x=dates, y=scores, mode="lines+markers",
        line=dict(color="#2FD3E8", width=2),
        marker=dict(size=10, color=colors_, line=dict(width=1, color="#0B1C2C")),
        hovertemplate="%{x}<br>Score: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(**_base_layout("Risk Score Trend Over Time", height=380))
    fig.update_xaxes(gridcolor=GRID_COLOR, title="Assessment Date")
    fig.update_yaxes(gridcolor=GRID_COLOR, range=[0, 100], title="Overall Score")
    return fig


def comparison_bar_chart(labels, before_scores, after_scores) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=before_scores, name="Previous",
        marker=dict(color="#5a7a91"),
    ))
    fig.add_trace(go.Bar(
        x=labels, y=after_scores, name="Current",
        marker=dict(color="#2FD3E8"),
    ))
    fig.update_layout(barmode="group", **_base_layout("Before vs. Current Comparison", height=400))
    fig.update_xaxes(gridcolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, range=[0, 100], title="Score")
    return fig
