exports.handler = async function(event) {
  const RAILWAY = 'https://limitless-mvp-production.up.railway.app';
  const qs = event.rawQuery || '';
  
  try {
    const res = await fetch(`${RAILWAY}/?${qs}`);
    const text = await res.text();
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: text,
    };
  } catch(e) {
    return {
      statusCode: 500,
      body: JSON.stringify({ ok: false, error: e.message }),
    };
  }
};
