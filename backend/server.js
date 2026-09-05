import express from 'express';

const app = express();
app.use(express.json({ limit: '2mb' }));
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

const PORT = process.env.PORT || 3000;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || '';
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || '';
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY || '';

function availableProviders() {
  return {
    gemini: Boolean(GEMINI_API_KEY),
    openai: Boolean(OPENAI_API_KEY),
    claude: Boolean(ANTHROPIC_API_KEY),
    deepseek: Boolean(DEEPSEEK_API_KEY),
  };
}

async function callGemini(message) {
  if (!GEMINI_API_KEY) throw new Error('Gemini ist noch nicht eingerichtet.');
  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${encodeURIComponent(GEMINI_API_KEY)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contents: [{ role: 'user', parts: [{ text: message }] }] })
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || 'Gemini API-Fehler');
  return data?.candidates?.[0]?.content?.parts?.map(p => p.text).filter(Boolean).join('\n') || 'Keine Antwort erhalten.';
}

async function callOpenAI(message) {
  if (!OPENAI_API_KEY) throw new Error('OpenAI ist noch nicht eingerichtet.');
  const r = await fetch('https://api.openai.com/v1/responses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({ model: 'gpt-5-mini', input: message })
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || 'OpenAI API-Fehler');
  return data?.output_text || data?.output?.flatMap(x => x.content || []).map(x => x.text).filter(Boolean).join('\n') || 'Keine Antwort erhalten.';
}

async function callClaude(message) {
  if (!ANTHROPIC_API_KEY) throw new Error('Claude ist noch nicht eingerichtet.');
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({ model: 'claude-sonnet-4-20250514', max_tokens: 1200, messages: [{ role: 'user', content: message }] })
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || 'Anthropic API-Fehler');
  return data?.content?.map(x => x.text).filter(Boolean).join('\n') || 'Keine Antwort erhalten.';
}

async function callDeepSeek(message) {
  if (!DEEPSEEK_API_KEY) throw new Error('DeepSeek ist noch nicht eingerichtet.');
  const r = await fetch('https://api.deepseek.com/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${DEEPSEEK_API_KEY}` },
    body: JSON.stringify({ model: 'deepseek-chat', messages: [{ role: 'user', content: message }], max_tokens: 1200 })
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || 'DeepSeek API-Fehler');
  return data?.choices?.[0]?.message?.content || 'Keine Antwort erhalten.';
}

async function callProvider(provider, message) {
  if (provider === 'gemini') return callGemini(message);
  if (provider === 'openai') return callOpenAI(message);
  if (provider === 'claude') return callClaude(message);
  if (provider === 'deepseek') return callDeepSeek(message);
  throw new Error('Unbekannter Provider.');
}

app.get('/health', (req, res) => {
  res.json({ ok: true, service: 'Sumski AI Backend', providers: availableProviders() });
});

app.post('/chat', async (req, res) => {
  try {
    const message = String(req.body?.message || '').trim();
    const mode = String(req.body?.mode || 'gratis').toLowerCase();
    const provider = String(req.body?.provider || '').toLowerCase();
    if (!message) return res.status(400).json({ ok: false, error: 'Nachricht fehlt.' });

    const available = availableProviders();

    if (mode === 'bestmix') {
      const enabled = ['gemini', 'openai', 'claude', 'deepseek'].filter(p => available[p]);
      if (!enabled.length) throw new Error('Noch kein API-Provider eingerichtet.');
      const results = await Promise.all(enabled.map(async p => {
        try { return { provider: p, answer: await callProvider(p, message) }; }
        catch (e) { return { provider: p, error: e.message }; }
      }));
      const successful = results.filter(x => x.answer);
      const synthesis = successful.length === 1
        ? successful[0].answer
        : successful.map(x => `${x.provider.toUpperCase()}: ${x.answer}`).join('\n\n');
      return res.json({ ok: true, mode: 'bestmix', results, answer: synthesis });
    }

    let selected = provider;
    if (!selected) {
      if (mode === 'gratis') selected = 'gemini';
      else if (mode === 'auto') selected = available.gemini ? 'gemini' : (available.deepseek ? 'deepseek' : (available.openai ? 'openai' : 'claude'));
      else selected = 'gemini';
    }

    const answer = await callProvider(selected, message);
    res.json({ ok: true, mode, provider: selected, answer });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message || 'Unbekannter Fehler' });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Sumski AI Backend läuft auf Port ${PORT}`);
});
