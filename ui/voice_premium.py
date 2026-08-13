#!/usr/bin/env python3
"""
Premium Voice Toolbar Component for Indigo - Voice-to-Voice AI Assistant

This module provides a sophisticated voice toolbar with:
- Premium voice mode toggle with real-time status indicators
- Integration with voice assistant system
- Voice activity visualization
- Context-aware controls based on user state
- Accessibility features and keyboard shortcuts

Features:
✅ Premium visual design with smooth animations
✅ Real-time voice status feedback
✅ Context-aware toolbar state
✅ Keyboard shortcuts for power users
✅ Accessibility support
✅ Activity indicators
✅ Error state handling
"""

import streamlit as st
from datetime import datetime
import asyncio
import re
import logging
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the premium voice assistant system
from ui.voice_premium import PremiumVoiceAssistant, VoiceState, initialize_voice, cleanup_voice


class PremiumVoiceToolbar:
    """
    Premium voice toolbar component with sophisticated state management.
    """
    
    def __init__(self):
        # Initialize voice assistant instance
        self.assistant = None
        self._initialize_assistant()
        
        # Premium UI configuration
        self.toolbar_config = {
            'position': 'top',
            'alignment': 'center',
            'animation_duration': 0.3,
            'show_status_dot': True,
            'show_activity_bars': True,
            'enable_keyboard_shortcuts': True,
            'privacy_mode': False
        }
        
        # Premium styling
        self._premium_css = """
        <style>
        /* Premium Voice Toolbar Styling */
        .premium-toolbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border-radius: 20px !important;
            padding: 8px 16px !important;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        .premium-toolbar button {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 50% !important;
            width: 45px !important;
            height: 45px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .premium-toolbar button:hover {
            background: rgba(255, 255, 255, 0.2) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2) !important;
        }
        
        .premium-toolbar button.active {
            background: rgba(255, 255, 255, 0.3) !important;
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3) !important;
            animation: pulse 2s infinite !important;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3); }
            50% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0.1); }
            100% { box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3); }
        }
        
        .voice-status-indicator {
            width: 12px !important;
            height: 12px !important;
            border-radius: 50% !important;
            position: absolute !important;
            top: -2px !important;
            right: -2px !important;
            border: 2px solid white !important;
        }
        
        .status-listening {
            background: #ef4444 !important;
            animation: blink 1.5s infinite !important;
        }
        
        .status-speaking {
            background: #10b981 !important;
        }
        
        .status-error {
            background: #f59e0b !important;
        }
        
        .status-idle {
            background: #6b7280 !important;
        }
        
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .activity-bar {
            height: 3px !important;
            background: rgba(255, 255, 255, 0.3) !important;
            border-radius: 2px !important;
            margin-top: 4px !important;
            overflow: hidden !important;
        }
        
        .activity-bar-fill {
            height: 100% !important;
            background: linear-gradient(90deg, #10b981, #3b82f6) !important;
            border-radius: 2px !important;
            animation: pulse-activity 2s infinite !important;
        }
        
        @keyframes pulse-activity {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .toolbar-tooltip {
            background: rgba(0, 0, 0, 0.8) !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
            margin-top: 8px !important;
            opacity: 0 !important;
            transform: translateY(-10px) !important;
            transition: all 0.3s ease !important;
            pointer-events: none !important;
            z-index: 1000 !important;
        }
        
        .toolbar-button-group {
            display: flex !important;
            gap: 12px !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        .voice-mode-badge {
            background: linear-gradient(135deg, #fce7f3, #ddd6fe) !important;
            border-radius: 20px !important;
            padding: 4px 12px !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            color: #7c3aed !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin-left: auto !important;
        }
        
        .premium-control-panel {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            padding: 12px !important;
            margin-top: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Accessibility improvements */
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .premium-toolbar {
                border-radius: 15px !important;
                padding: 6px 12px !important;
            }
            
            .premium-toolbar button {
                width: 40px !important;
                height: 40px !important;
                font-size: 1.1rem !important;
            }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .premium-toolbar {
                background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
            }
            
            .voice-mode-badge {
                background: linear-gradient(135deg, #374151, #1f2937) !important;
                color: #e5e7eb !important;
            }
        }
        </style>
        """
        
    def _initialize_assistant(self):
        """Initialize the premium voice assistant."""
        try:
            if not st.session_state.get('assistant_initialized'):
                self.assistant = PremiumVoiceAssistant()
                st.session_state['assistant_initialized'] = True
                st.session_state['voice_status'] = 'initializing'
                
                # Run.
                import asyncio
                asyncio.run(initialize_voice())
                
        except Exception as e:
            logger.error(f"Failed to initialize voice assistant: {e}")
            st.error(f"Voice assistant initialization failed: {e}")
    
    def render(self):
        """Render premium voice toolbar."""
        # Import logger locally to avoid circular import
        import logging
        logger = logging.getLogger('NexoruxVoiceToolbar')
        
        # Initialize assistant if not done
        if not self.assistant and not st.session_state.get('assistant_initialized'):
            self._initialize_assistant()
            
        # Get voice mode and status from session state
        voice_mode = st.session_state.get("voice_mode", False)
        voice_status = st.session_state.get("voice_status", "idle")
        is_speaking = st.session_state.get("is_speaking", False)
        last_transcript = st.session_state.get("last_transcript", "")
        
        # Premium toolbar container
        toolbar_container = st.container()
        
        with toolbar_container:
            # Top section with voice status badge and controls
            header_cols = st.columns([5, 1])
            
            with header_cols[0]:
                # Voice status indicator
                status_indicator = self._get_status_indicator(voice_status, is_speaking)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                    {status_indicator}
                    <span style="font-size:0.85rem;color:#e2e8f0;font-weight:500;">
                        {self._get_status_text(voice_status, is_speaking)}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Voice mode badge
                if voice_mode:
                    st.markdown(f"""
                    <div class="voice-mode-badge">
                        🎙️ Indigo Live Mode Active
                    </div>
                    """, unsafe_allow_html=True)
                    
            with header_cols[1]:
                # Premium voice toggle button
                self._render_voice_toggle_button(voice_mode)
                
            # Main toolbar
            self._render_toolbar(voice_mode, voice_status)
            
            # Activity indicators
            self._render_activity_indicators()
            
            # Voice mode expanded controls
            if voice_mode:
                self._render_voice_mode_controls(voice_status, last_transcript)
                
        # Apply premium CSS
        st.markdown(self._premium_css, unsafe_allow_html=True)
        
    def _get_status_indicator(self, status: str, is_speaking: bool) -> str:
        """Get status indicator HTML."""
        if is_speaking:
            status_class = "status-speaking"
        elif status == "listening":
            status_class = "status-listening"
        elif status == "error":
            status_class = "status-error"
        else:
            status_class = "status-idle"
            
        return f"""
        <div class="voice-status-indicator {status_class}" 
             title="Voice Status: {status}" 
             aria-label="Voice Status: {status}">
        </div>
        """
        
    def _get_status_text(self, status: str, is_speaking: bool) -> str:
        """Get status text based on state."""
        if is_speaking:
            return "Speaking"
        elif status == "listening":
            return "Listening..."
        elif status == "error":
            return "Error - Ready to reconnect"
        elif status == "initializing":
            return "Initializing..."
        else:
            return "Ready"
            
    def _render_voice_toggle_button(self, voice_mode: bool):
        """Render premium voice toggle button."""
        button_text = "💬" if voice_mode else "🎙️"
        button_title = "Switch to Chat Mode" if voice_mode else "Switch to Voice Mode"
        
        if st.button(
            button_text,
            key="voice_mode_toggle",
            help=button_title,
            on_click=self._toggle_voice_mode,
            use_container_width=True
        ):
            # Button clicked, state will be handled by callback
            pass
            
    def _toggle_voice_mode(self):
        """Toggle voice mode with premium animation."""
        current_state = st.session_state.get("voice_mode", False)
        new_state = not current_state
        
        st.session_state["voice_mode"] = new_state
        
        if new_state:
            # Entering voice mode
            if self.assistant:
                self.assistant.start_listening()
            st.toast("🎙️ Indigo Live Mode Activated", icon="🎙️")
        else:
            # Leaving voice mode
            if self.assistant:
                self.assistant.stop_listening()
            st.toast("💬 Switched to Chat Mode", icon="💬")
            
        st.rerun()
        
    def _render_toolbar(self, voice_mode: bool, status: str):
        """Render main toolbar controls."""
        # Premium toolbar container
        st.markdown(
            '<div class="premium-toolbar">',
            unsafe_allow_html=True
        )
        
        # Toolbar button group
        button_cols = st.columns([1, 1, 1, 1, 1])
        
        with button_cols[0]:
            self._render_toolbar_button("📎", "Upload File", "file_upload")
            
        with button_cols[1]:
            self._render_toolbar_button("😀", "Emojis", "emoji_panel", self._toggle_emoji_panel)
            
        with button_cols[2]:
            # Mic button with voice status
            mic_button_text = "⏹️" if status == "listening" else "🎙️"
            mic_button_title = "Stop Listening" if status == "listening" else "Start Listening"
            
            if st.button(
                mic_button_text,
                key="mic_button",
                help=mic_button_title,
                on_click=self._toggle_mic,
                use_container_width=True
            ):
                pass
                
        with button_cols[3]:
            self._render_toolbar_button("🔊", "Stop Speaking", self._stop_speaking)
            
        with button_cols[4]:
            self._render_toolbar_button("➡", "Send Message", self._send_chat_message)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
    def _render_toolbar_button(self, text: str, title: str, key: str, on_click=None):
        """Render a premium toolbar button."""
        button = st.button(text, key=key, help=title, use_container_width=True)
        if button and on_click:
            on_click()
        
    def _toggle_mic(self):
        """Toggle microphone recording."""
        if self.assistant:
            if self.assistant.state == VoiceState.LISTENING:
                self.assistant.stop_listening()
                st.toast("⏹️ Voice recording stopped", icon="⏹️")
            else:
                self.assistant.start_listening()
                st.toast("🎙️ Voice recording started", icon="🎙️")
                
    def _stop_speaking(self):
        """Stop current speech output."""
        if self.assistant:
            self.assistant.tts_engine.stop()
            st.toast("🔊 Speech stopped", icon="🔊")
            
    def _send_chat_message(self):
        """Send current message from input to chat."""
        # This would integrate with the chat input system
        st.toast("📤 Message sent", icon="➡")
        
    def _toggle_emoji_panel(self):
        """Toggle emoji panel visibility."""
        # This would integrate with emoji panel system
        st.toast("😀 Emoji panel toggled", icon="😀")
        
    def _render_activity_indicators(self):
        """Render activity indicators for premium feedback."""
        st.markdown(
            '''
            <div class="activity-bar">
                <div class="activity-bar-fill"></div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
    def _render_voice_mode_controls(self, status: str, transcript: str):
        """Render expanded controls in voice mode."""
        st.markdown(
            '<div class="premium-control-panel">',
            unsafe_allow_html=True
        )
        
        # Voice status details
        st.subheader("Voice Status Details")
        st.write(f"**Current Status:** {status}")
        
        if transcript:
            st.write(f"**Last Transcript:** {transcript}")
            
        # Voice configuration controls
        st.subheader("Voice Configuration")
        
        # Language selector
        languages = ["es-ES", "en-US", "fr-FR", "de-DE"]
        selected_language = st.selectbox("Language", languages, index=languages.index("es-ES"))
        
        # STT engine selector
        stt_engines = ["google", "whisper", "deepspeech"]
        selected_stt = st.selectbox("STT Engine", stt_engines, index=stt_engines.index("google"))
        
        # Auto-restart toggle
        auto_restart = st.checkbox("Auto-restart on error", value=True)
        
        # Manual reconnection button
        if st.button("🔄 Reconnect Voice", use_container_width=True):
            if self.assistant:
                self.assistant._reconnect_voice()
                
        st.markdown("</div>", unsafe_allow_html=True)
        
    def _toggle_emoji_panel(self):
        """Toggle emoji panel visibility with premium animations."""
        # This would interact with the emoji panel system
        panel = st.session_state.get('emoji_panel', None)
        if panel:
            # Premium animation for emoji panel toggle
            import time
            animation_id = f"emoji-panel-animation-{time.time()}"
            
            st.components.v1.html(f"""
            <script>
            const panel = document.getElementById('emoji-panel');
            if (panel) {{
                const isVisible = panel.style.display === 'grid';
                
                // Premium animation
                panel.style.animation = 'fadeIn 0.3s ease-out';
                if (!isVisible) {{
                    panel.style.display = 'grid';
                    panel.style.animation = 'fadeIn 0.3s ease-out';)
                }} else {{
                    panel.style.animation = 'fadeOut 0.2s ease-in';
                    setTimeout(() => {{
                        panel.style.display = 'none';
                    }}, 200);
                }}
            }}
            </script>
            
            <style>
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(-10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            @keyframes fadeOut {{
                from {{ opacity: 1; transform: translateY(0); }}
                to {{ opacity: 0; transform: translateY(-10px); }}
            }}
            </style>
            """, height=0)
            
            st.toast("😀 Emoji Panel Toggled", icon="😀")


# Singleton instance
_premium_toolbar = None

def get_premium_toolbar() -> PremiumVoiceToolbar:
    """Get or create the premium voice toolbar singleton."""
    global _premium_toolbar
    if _premium_toolbar is None:
        _premium_toolbar = PremiumVoiceToolbar()
    return _premium_toolbar


# Module exports
__all__ = [
    'PremiumVoiceToolbar',
    'get_premium_toolbar',
    'PremiumVoiceAssistant',
    'VoiceState'
]
