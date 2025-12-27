import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import React from 'react';

export default function SentimentChart({ data }) {
  const chartData = Object.entries(data?.buckets || {}).map(([ts, val]) => ({
    timestamp: ts,
    ...val
  }));

  return (
    <div className="bg-gray-800 p-6 rounded-xl h-80">
      <h2 className="text-xl font-bold mb-4">Sentiment Trend</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="timestamp" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
          <Line type="monotone" dataKey="positive" stroke="#10b981" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}