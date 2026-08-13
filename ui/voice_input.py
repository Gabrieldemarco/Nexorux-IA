# -*- coding: utf-8 -*-
import streamlit as st


def render_voice_input(voice_mode: bool = False):
    vm = "true" if voice_mode else "false"

    html = f"""<div style="display:flex;align-items:center;gap:2px;padding:4px 12px;height:42px;
max-width:760px;margin:0 auto;box-sizing:border-box;">
  <button id="v-attach" style="width:34px;height:34px;border:none;border-radius:50%;background:transparent;
cursor:pointer;font-size:1.4rem;color:#64748b;display:flex;align-items:center;justify-content:center;
flex-shrink:0;" title="Adjuntar archivo">+</button>
  <button id="v-emoji" style="width:34px;height:34px;border:none;border-radius:50%;background:transparent;
cursor:pointer;font-size:1.2rem;color:#64748b;display:flex;align-items:center;justify-content:center;
flex-shrink:0;" title="Emojis">😀</button>
  <div style="flex:1;min-width:0;"></div>
  <button id="v-mic" style="width:36px;height:36px;border:none;border-radius:50%;background:transparent;
cursor:pointer;font-size:1.4rem;color:#64748b;display:flex;align-items:center;justify-content:center;
flex-shrink:0;transition:all 0.15s;" title="Dictado por voz">🎙</button>
  <button id="v-send" style="width:36px;height:36px;border:none;border-radius:50%;background:#3b82f6;
color:#fff;cursor:pointer;font-size:1.2rem;display:none;align-items:center;justify-content:center;
flex-shrink:0;box-shadow:0 2px 8px rgba(59,130,246,0.35);" title="Enviar">➡</button>
</div>

<style>
#v-mic.recording {{ background:#ef4444 !important; color:#fff !important; animation:pulseV 0.8s infinite; }}
#v-mic.done {{ background:#10b981 !important; color:#fff !important; }}
@keyframes pulseV {{ 0%{{box-shadow:0 0 0 0 rgba(239,68,68,0.5)}} 70%{{box-shadow:0 0 0 8px rgba(239,68,68,0)}} 100%{{box-shadow:0 0 0 0 rgba(239,68,68,0)}} }}
</style>

<script>
(function() {{
  var top = window.top;
  var parentDoc = top.document;
  var SR = top.SpeechRecognition || top.webkitSpeechRecognition;
  var vm = {vm};

  var doc = document;
  var mic = doc.getElementById('v-mic');
  var send = doc.getElementById('v-send');
  var attach = doc.getElementById('v-attach');
  var emojiBtn = doc.getElementById('v-emoji');

  // Shared API for cross-iframe TTS coordination
  top._nexoruxToolbar = {{
    cancelTTS: function() {{ var ss = top.speechSynthesis; if (ss) ss.cancel(); }},
    _ttsActive: false,
    _ttsCancelRequested: false,
  }};

  function ta() {{
    var ci = parentDoc.querySelector('[data-testid="stChatInput"]');
    return ci ? ci.querySelector('textarea') : null;
  }}

  function setVal(txt) {{
    var t = ta(); if (!t) return;
    var p = Object.getPrototypeOf(t);
    var s = Object.getOwnPropertyDescriptor(p, 'value').set;
    s.call(t, txt);
    t.dispatchEvent(new InputEvent('input', {{bubbles:true, inputType:'insertText', data:txt}}));
  }}

  function submitMsg() {{
    var t = ta(); if (!t || !t.value.trim()) return;
    var btn = parentDoc.querySelector('[data-testid="stChatInputSubmitButton"]');
    if (btn) {{ btn.click(); return; }}
    t.dispatchEvent(new KeyboardEvent('keydown', {{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true,cancelable:true}}));
  }}

  function updateUI() {{
    var t = ta();
    var hasText = t && t.value.trim() !== '';
    mic.style.display = hasText ? 'none' : 'flex';
    send.style.display = hasText ? 'flex' : 'none';
  }}

  var state = 'idle', rec = null, _micDenied = false;
  function ui(s) {{
    state = s; mic.className = '';
    if (s === 'idle') {{ mic.textContent = '🎙'; mic.title = 'Dictado por voz'; }}
    else if (s === 'recording') {{ mic.classList.add('recording'); mic.textContent = '⏹'; mic.title = 'Detener'; }}
    else if (s === 'done') {{ mic.classList.add('done'); mic.textContent = '📤'; mic.title = 'Enviar'; }}
  }}

  function cancelTTS() {{
    var ss = top.speechSynthesis;
    if (ss && ss.speaking) {{
      ss.cancel();
      if (top._nexoruxToolbar) top._nexoruxToolbar._ttsActive = false;
    }}
  }}

  function startRec() {{
    if (!SR || _micDenied) return;
    if (rec) {{ try {{ rec.stop(); }} catch(e) {{ }} rec = null; }}
    cancelTTS();
    var frame = window.frameElement;
    if (frame) frame.setAttribute('allow', 'microphone');
    rec = new SR();
    rec.lang = 'es-ES';
    rec.interimResults = false;
    rec.continuous = false;
    rec.onstart = function() {{ ui('recording'); }};
    rec.onend = function() {{
      // onend fires after onresult (speech) OR on timeout (silence)
      if (state === 'recording') {{
        rec = null;
        if (vm) {{ ui('idle'); startRec(); }}
        else {{ ui('done'); }}
      }}
    }};
    rec.onerror = function(e) {{
      rec = null;
      if (e.error === 'not-allowed') {{
        _micDenied = true;
        alert('Microfono denegado. Habilitalo desde el candado en la barra.');
        ui('idle');
      }} else {{
        ui('idle');
      }}
    }};
    rec.onresult = function(e) {{
      var txt = e.results[0][0].transcript;
      rec = null;
      cancelTTS();
      if (vm) {{
        // set value, wait for React to flush state, then submit
        setVal(txt);
        setTimeout(function() {{
          var t = ta();
          if (t && t.value.trim()) submitMsg();
        }}, 0);
      }} else {{
        setVal(txt);
        ui('done');
        updateUI();
      }}
    }};
    try {{ rec.start(); }} catch(e) {{ rec = null; ui('idle'); _micDenied = true; }}
  }}

  function stopRec() {{
    if (rec) {{ try {{ rec.stop(); }} catch(e) {{ }} rec = null; }}
    ui('idle');
  }}

  // Emoji panel (created once in parent document)
  var panel = parentDoc.getElementById('v-emoji-panel');
  if (!panel) {{
    panel = parentDoc.createElement('div');
    panel.id = 'v-emoji-panel';
    panel.style.cssText = 'display:none;position:fixed;bottom:140px;left:50%;transform:translateX(-50%);z-index:999999;background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);padding:8px;grid-template-columns:repeat(6,32px);gap:4px;max-width:230px;';
    parentDoc.body.appendChild(panel);
  }}
  if (!panel._built) {{
    panel._built = true;
    var emojis = ['😀','😂','😍','😎','👍','🔥','🎉','🚀','❤️','👏','💡','👀','✨','🙏','😢','😡','😊','😋','😜','😉','👌','🤔','😈','🥰'];
    emojis.forEach(function(emoji){{
      var sp = parentDoc.createElement('span');
      sp.className = 'v-em-item';
      sp.style.cssText = 'font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;';
      sp.onmouseover = function(){{sp.style.background='#f1f5f9';}};
      sp.onmouseout = function(){{sp.style.background='transparent';}};
      sp.textContent = emoji;
      sp.onclick = function(){{ var t = ta(); if(t){{ var val = t.value, start = t.selectionStart, end = t.selectionEnd; setVal(val.substring(0,start) + emoji + val.substring(end)); t.setSelectionRange(start+emoji.length, start+emoji.length); t.focus(); }} panel.style.display = 'none'; }};
      panel.appendChild(sp);
    }});
  }}

  attach.onclick = function() {{
    var input = parentDoc.querySelector('[data-testid="stFileUploader"] input[type="file"]');
    if (input) input.click();
  }};

  emojiBtn.onclick = function(e) {{ e.stopPropagation(); panel.style.display = panel.style.display === 'grid' ? 'none' : 'grid'; }};

  mic.onclick = function() {{
    _micDenied = false;
    if (state === 'idle') startRec();
    else if (state === 'recording') stopRec();
    else if (state === 'done') {{ var t = ta(); if (t && t.value.trim()) submitMsg(); }}
  }};

  send.onclick = function(e) {{ e.stopPropagation(); submitMsg(); }};

  parentDoc.addEventListener('click', function(e) {{ if (panel && !panel.contains(e.target) && e.target !== emojiBtn) panel.style.display = 'none'; }});

  // Watch for chat input textarea and sync button visibility
  (function initWatch() {{
    var t = ta();
    if (t && !t._nexoruxW) {{ t._nexoruxW = true; t.addEventListener('input', updateUI); t.addEventListener('keyup', updateUI); updateUI(); }}
    else setTimeout(initWatch, 300);
  }})();

  // Voice mode: keep recording alive with auto-restart
  if (vm && SR) {{
    (function keepAlive() {{
      if (state === 'idle' && !_micDenied) startRec();
      setTimeout(keepAlive, 3000);
    }})();
  }}
}})();
</script>"""
    st.components.v1.html(html, height=56)
