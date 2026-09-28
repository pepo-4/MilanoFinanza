"""
Package UI: Componenti di presentazione utente (Streamlit e HTML interattivo).
"""

from .streamlit_views import render_fear_and_greed_section, render_ai_executive_summary
from .standalone_html import generate_decision_support_html

__all__ = [
    "render_fear_and_greed_section",
    "render_ai_executive_summary",
    "generate_decision_support_html",
]
