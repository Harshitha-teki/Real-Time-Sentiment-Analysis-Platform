export const fetchDashboardData = async (period = 'minute') => {
  try {
    // Fetch distribution, aggregate (buckets), and recent posts so the UI has everything it needs
    const [distRes, aggRes, postsRes] = await Promise.all([
      fetch('http://localhost:8000/api/sentiment/distribution'),
      fetch(`http://localhost:8000/api/sentiment/aggregate?period=${period}`),
      fetch('http://localhost:8000/api/posts?limit=10')
    ]);

    if (!distRes.ok || !aggRes.ok || !postsRes.ok) {
      console.error('One or more dashboard API calls failed', { distRes, aggRes, postsRes });
      throw new Error('Dashboard API failure');
    }

    const dist = await distRes.json();
    const agg = await aggRes.json();
    const posts = await postsRes.json();

    return {
      distribution: dist.distribution || {},
      buckets: agg.data || [],
      posts: posts.posts || []
    };
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
    return { distribution: {}, buckets: [], posts: [] };
  }
};

// Opens a WebSocket to the backend and forwards parsed messages to the provided
// callback. Returns the WebSocket instance so the caller can close it.
export const connectWebSocket = (onMessage) => {
  try {
    const ws = new WebSocket('ws://localhost:8000/ws/sentiment');

    ws.onopen = () => console.info('WebSocket connected to backend');

    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data);
        if (typeof onMessage === 'function') onMessage(payload);
      } catch (err) {
        console.error('Failed to parse WS message', err);
      }
    };

    ws.onerror = (err) => console.error('WebSocket error', err);
    ws.onclose = () => console.info('WebSocket closed');

    return ws;
  } catch (e) {
    console.error('connectWebSocket failed', e);
    return null;
  }
};