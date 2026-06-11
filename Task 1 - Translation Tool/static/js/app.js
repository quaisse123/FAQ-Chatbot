document.addEventListener('DOMContentLoaded', () => {
  const sourceText = document.getElementById('sourceText');
  const translatedTextDiv = document.getElementById('translatedText');
  const translateBtn = document.getElementById('translateBtn');
  const copyBtn = document.getElementById('copyBtn');
  const speakBtn = document.getElementById('speakBtn');
  const swapBtn = document.getElementById('swapBtn');
  const clearBtn = document.getElementById('clearBtn');
  const sourceLang = document.getElementById('sourceLang');
  const targetLang = document.getElementById('targetLang');
  const status = document.getElementById('status');
  const charCountLive = document.getElementById('charCountLive');
  const charCount = document.getElementById('charCount');

  // Character counter
  sourceText.addEventListener('input', () => {
    const len = sourceText.value.length;
    charCountLive.textContent = len;
    charCount.textContent = len;
  });

  async function translate() {
    const text = sourceText.value.trim();
    if (!text) {
      status.textContent = '📝 Enter some text to translate';
      return;
    }

    status.textContent = '⏳ Translating...';
    translateBtn.disabled = true;
    translateBtn.style.opacity = '0.6';

    try {
      const res = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, source: sourceLang.value, target: targetLang.value })
      });

      if (!res.ok) {
        const err = await res.json();
        status.textContent = `❌ ${err.detail || 'Translation failed'}`;
        translatedTextDiv.innerHTML = '<span class="placeholder-text">Translation failed. Please try again.</span>';
      } else {
        const data = await res.json();
        translatedTextDiv.textContent = data.translated_text || '';
        status.textContent = data.detected_source ? `✓ Detected: ${data.detected_source}` : '✓ Done';
      }
    } catch (e) {
      status.textContent = '❌ Network error';
      translatedTextDiv.innerHTML = '<span class="placeholder-text">Network error. Please check your connection.</span>';
    } finally {
      translateBtn.disabled = false;
      translateBtn.style.opacity = '1';
    }
  }

  translateBtn.addEventListener('click', translate);

  sourceText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      translate();
    }
  });

  copyBtn.addEventListener('click', async () => {
    const txt = translatedTextDiv.textContent || '';
    if (!txt || txt.includes('Translation will appear here')) {
      status.textContent = '⚠️ No translation to copy';
      return;
    }
    try {
      await navigator.clipboard.writeText(txt);
      copyBtn.textContent = '✓ Copied';
      setTimeout(() => {
        copyBtn.textContent = '📋 Copy';
      }, 2000);
      status.textContent = '✓ Copied to clipboard';
    } catch {
      status.textContent = '❌ Copy failed';
    }
  });

  speakBtn.addEventListener('click', () => {
    const txt = translatedTextDiv.textContent || '';
    if (!txt || txt.includes('Translation will appear here')) {
      status.textContent = '⚠️ No translation to speak';
      return;
    }
    try {
      const utter = new SpeechSynthesisUtterance(txt);
      utter.lang = targetLang.value === 'auto' ? 'en-US' : targetLang.value;
      speakBtn.textContent = '⏸️ Stop';
      utter.onend = () => {
        speakBtn.textContent = '🔊 Listen';
      };
      speechSynthesis.cancel();
      speechSynthesis.speak(utter);
    } catch {
      status.textContent = '❌ Text-to-speech not available';
    }
  });

  swapBtn.addEventListener('click', () => {
    const s = sourceLang.value;
    const t = targetLang.value;
    
    // Prevent swapping if target is 'auto'
    if (t === 'auto') {
      status.textContent = '⚠️ Cannot swap: target cannot be "auto"';
      return;
    }

    sourceLang.value = t;
    targetLang.value = s;
    const st = sourceText.value;
    const rt = translatedTextDiv.textContent;
    sourceText.value = rt;
    translatedTextDiv.textContent = st || '';
    charCountLive.textContent = rt.length;
    charCount.textContent = rt.length;
    status.textContent = '⇅ Languages swapped';
    
    // Auto-translate if there's translated text
    if (rt && !rt.includes('Translation will appear')) {
      translate();
    }
  });

  clearBtn.addEventListener('click', () => {
    sourceText.value = '';
    translatedTextDiv.innerHTML = '<span class="placeholder-text">Translation will appear here...</span>';
    status.textContent = '';
    charCountLive.textContent = '0';
    charCount.textContent = '0';
    clearBtn.textContent = '🗑️ Clear';
    setTimeout(() => {
      clearBtn.textContent = '🗑️ Clear';
    }, 500);
  });
});
