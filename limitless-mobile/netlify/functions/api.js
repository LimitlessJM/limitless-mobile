exports.handler = async function(event) {
  const RAILWAY = 'https://web-production-e8a11.up.railway.app';
  const API_PORT = '';
  
  // Map tool names to FastAPI endpoints
  const toolMap = {
    'api_health':      { method: 'GET',  path: '/health' },
    'api_my_jobs':     { method: 'GET',  path: '/my-jobs' },
    'api_clock_in':    { method: 'POST', path: '/clock-in' },
    'api_clock_out':   { method: 'POST', path: '/clock-out' },
    'api_get_week':    { method: 'GET',  path: '/get-week' },
    'api_submit_week': { method: 'POST', path: '/submit-week' },
    'api_login':       { method: 'POST', path: '/login' },
    'api_create_user': { method: 'POST', path: '/create-user' },
  };

  const params = new URLSearchParams(event.rawQuery || '');
  const tool = params.get('tool');
  const route = toolMap[tool];

  if (!route) {
    return { statusCode: 400, body: JSON.stringify({ ok: false, error: 'Unknown tool' }) };
  }

  // Build query string without 'tool' param
  params.delete('tool');
  const qs = params.toString();
  const url = `${RAILWAY}${API_PORT}${route.path}${qs ? '?' + qs : ''}`;

  try {
    let fetchOpts = { method: route.method, headers: { 'Content-Type': 'application/json' } };
    
    // For POST endpoints that take body params (login, create-user)
    if (route.method === 'POST' && (tool === 'api_login' || tool === 'api_create_user')) {
      const body = {};
      params.forEach((v, k) => body[k] = v);
      fetchOpts.body = JSON.stringify(body);
      fetchOpts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
      const res = await fetch(`${RAILWAY}${API_PORT}${route.path}`, fetchOpts);
      const data = await res.json();
      return { statusCode: 200, headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(data) };
    }

    const res = await fetch(url, fetchOpts);
    const data = await res.json();
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify(data),
    };
  } catch(e) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ok: false, error: e.message }),
    };
  }
};
