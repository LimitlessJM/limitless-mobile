exports.handler = async function(event) {
  const RAILWAY = 'https://limitless-mvp-production.up.railway.app';

  const params = new URLSearchParams(event.rawQuery || '');
  const tool = params.get('tool');

  if (!tool || !tool.startsWith('api_')) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ok: false, error: 'Unknown tool' }),
    };
  }

  const qs = params.toString();
  const url = `${RAILWAY}/?${qs}`;

  try {
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'LJM-Mobile/1.0',
        'Accept': 'text/html,application/json',
      },
      redirect: 'follow',
    });

    const text = await res.text();

    // Extract JSON from Streamlit response
    // Streamlit renders JSON in a <pre> tag or as plain text
    let data = null;

    // Try to find JSON object in the response
    const patterns = [
      /\{"ok"[\s\S]*?\}(?=\s*<|\s*$)/,  // JSON starting with {"ok"
      /(\{[\s\S]*?"ok"[\s\S]*?\})/,       // Any JSON with "ok" key
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        try {
          data = JSON.parse(match[0]);
          break;
        } catch(e) {}
      }
    }

    // Try parsing the whole response as JSON
    if (!data) {
      try { data = JSON.parse(text); } catch(e) {}
    }

    if (!data) {
      // Return the raw text for debugging
      data = { ok: false, error: 'Could not parse response', raw: text.slice(0, 500) };
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify(data),
    };
  } catch(e) {
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ok: false, error: e.message }),
    };
  }
};
