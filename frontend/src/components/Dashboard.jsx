import React, { useState, useEffect } from 'react';
import { fetchDashboardData, connectWebSocket } from '../services/api';
import DistributionChart from './DistributionChart';
import SentimentChart from './SentimentChart';

export default function Dashboard() {
  // Initialize with empty array to prevent .map() crash
  const [data, setData] = useState({ distribution: {}, buckets: {}, posts: [] });

  useEffect(() => {
    // Phase 5.3: Ensure we pass 'minute' to avoid 422 error
    fetchDashboardData('minute').then(res => {
      if (res) {
        setData({
          distribution: res.distribution || {},
          buckets: res.buckets || {},
          posts: Array.isArray(res.posts) ? res.posts : []
        });
      }
    });

    const socket = connectWebSocket((msg) => {
      // Backend broadcasts messages with type 'new_post' and data payload.
      // Accept both 'post' and 'new_post' to be resilient.
      if (!msg) return;
      const t = msg.type || msg?.data?.type || null;
      if (t === 'post' || t === 'new_post') {
        const payload = msg.data || msg;
        setData(prev => ({
          ...prev,
          posts: [payload, ...(prev.posts || [])].slice(0, 10)
        }));
      }
    });
    return () => socket?.close();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8">Sentiment Analysis Live</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <DistributionChart data={data} />
        <div className="bg-gray-800 p-6 rounded-xl h-80 overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">Live Feed</h2>
          {/* Safeguard: only map if posts is an array */}
          {data.posts && data.posts.length > 0 ? (
            data.posts.map((p, i) => (
              <div key={i} className="mb-3 p-3 bg-gray-700 rounded-lg border-l-4 border-blue-500">
                <span className="font-bold uppercase text-xs mr-2" style={{color: p.sentiment === 'positive' ? '#10b981' : '#ef4444'}}>
                  {p.sentiment}
                </span>
                {p.content || p.text}
              </div>
            ))
          ) : (
            <p className="text-gray-500 italic">Waiting for incoming data...</p>
          )}
        </div>
      </div>
      <SentimentChart data={data} />
    </div>
  );
}