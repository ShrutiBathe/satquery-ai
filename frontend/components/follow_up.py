from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Follow-up Conversational Chat Component
Allows users to ask follow-up questions about the active analysis result.
"""

import streamlit as st
from typing import Dict, Any
from datetime import datetime

from services.api_client import client


def render_follow_up_chat(analysis_result: Dict[str, Any]) -> None:
    """Render follow-up conversation thread and question composer."""
    render_html("""
<div style="margin-top: 1.8rem; border-top: 1px solid rgba(56, 189, 248, 0.15); padding-top: 1.2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
        <div>
            <h3 style="font-size: 1.15rem; margin: 0 0 0.2rem 0; font-weight: 700; color: #F8FAFC;">
                Ask a Follow-Up Inquiry
            </h3>
            <p style="font-size: 0.82rem; color: #94A3B8; margin: 0;">
                Inquire further about specific coordinates, dimensions, or anomaly details in this scene.
            </p>
        </div>
        <span class="sq-badge sq-badge-cyan">INTERACTIVE CHAT</span>
    </div>
</div>
""")

    chat_history = st.session_state.get("follow_up_chat", [])

    # Render previous follow-up exchange
    if chat_history:
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content")
            t_str = msg.get("time", "")

            if role == "user":
                render_html(f"""
<div style="display: flex; justify-content: flex-end; margin-bottom: 0.7rem;">
    <div style="background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 12px 12px 2px 12px; padding: 0.7rem 1rem; max-width: 80%;">
        <div style="font-size: 0.72rem; color: #00F0FF; font-family: monospace; margin-bottom: 2px;">YOU • {t_str}</div>
        <div style="color: #F8FAFC; font-size: 0.9rem;">{content}</div>
    </div>
</div>
""")
            else:
                render_html(f"""
<div style="display: flex; justify-content: flex-start; margin-bottom: 0.7rem;">
    <div style="background: rgba(14, 22, 43, 0.85); border: 1px solid rgba(56, 189, 248, 0.22); border-radius: 12px 12px 12px 2px; padding: 0.7rem 1rem; max-width: 85%;">
        <div style="font-size: 0.72rem; color: #38BDF8; font-family: monospace; margin-bottom: 2px;">SATQUERY AI ASSISTANT • {t_str}</div>
        <div style="color: #F8FAFC; font-size: 0.9rem; line-height: 1.5;">{content}</div>
    </div>
</div>
""")

    # Input and Send button
    c_input, c_btn = st.columns([4, 1])

    with c_input:
        user_msg = st.text_input(
            label="Follow-up question",
            placeholder="e.g., What about the southern sector? Or estimate the area of the largest structure...",
            key="input_follow_up_msg",
            label_visibility="collapsed"
        )

    with c_btn:
        if st.button("Send Inquiry 💬", use_container_width=True, key="btn_send_follow_up"):
            if user_msg.strip():
                now_str = datetime.now().strftime("%H:%M:%S")
                chat_history.append({"role": "user", "content": user_msg.strip(), "time": now_str})

                # Dispatch via API client
                demo_mode = st.session_state.get("demo_mode", True)
                resp = client.send_follow_up(analysis_result, user_msg.strip(), demo_mode=demo_mode)
                bot_reply = resp.get("reply", "Analysis confirms telemetry is consistent with primary findings.")
                
                chat_history.append({"role": "assistant", "content": bot_reply, "time": now_str})
                st.session_state["follow_up_chat"] = chat_history
                st.rerun()
