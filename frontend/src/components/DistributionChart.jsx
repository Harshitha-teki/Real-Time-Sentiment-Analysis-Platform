import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import React from 'react';
const COLORS = { positive: '#10b981', negative: '#ef4444', neutral: '#6b7280' };

export default function DistributionChart({ data }) {
  const chartData = Object.entries(data.distribution || {}).map(([name, value]) => ({ name, value }));
  return (
    <div className="bg-gray-800 p-6 rounded-xl h-80">
      <h2 className="text-xl font-bold mb-4">Sentiment Split</h2>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={chartData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
            {chartData.map((entry) => <Cell key={entry.name} fill={COLORS[entry.name]} />)}
          </Pie>
          <Tooltip /><Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}