exports.handler = async function(event) {
  const BASE = 'https://web-production-e8a11.up.railway.app';

  const toolMap = {
    'api_health':             { method: 'GET',  path: '/health',      body: false },
    'api_my_jobs':            { method: 'GET',  path: '/my-jobs',     body: false },
    'api_clock_in':           { method: 'POST', path: '/clock-in',    body: false },
    'api_clock_out':          { method: 'POST', path: '/clock-out',   body: false },
    'api_get_week':           { method: 'GET',  path: '/get-week',    body: false },
    'api_submit_week':        { method: 'POST', path: '/submit-week', body: false },
    'api_login':              { method: 'POST', path: '/login',       body: true  },
    'api_create_mobile_user': { method: 'POST', path: '/create-user', body: true  },
  };

  const params = new URLSearchParams(event.rawQuery || '');
  const tool = params.get('tool');
  params.delete('tool');
  const route = toolMap[tool];

  if (!route) {
    return {
      statusCode: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ ok: false, error: 'Unknown tool: ' + tool }),
    };
  }

  try {
    let url, fetchOpts;

    if (route.body) {
      // POST with JSON body
      const bodyObj = {};
      params.forEach((v, k) => { bodyObj[k] = v; });
      url = BASE + route.path;
      fetchOpts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyObj),
      };
    } else {
      // GET or POST with query string
      const qs = params.toString();
      url = BASE + route.path + (qs ? '?' + qs : '');
      fetchOpts = {
        method: route.method,
        headers: { 'Content-Type': 'application/json' },
      };
    }

    const res = await fetch(url, fetchOpts);
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch(e) { data = { ok: false, error: text.slice(0, 200) }; }
    if (!res.ok && data.detail) data = { ok: false, error: data.detail };

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
