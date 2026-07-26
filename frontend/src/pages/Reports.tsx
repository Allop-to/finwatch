import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { transactionsApi, categoriesApi, detectionApi } from '@/api/client';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, PieChart, Pie, Cell,
} from 'recharts';
import type { Transaction } from '@/types';

const COLORS = ['#3b82f6','#ef4444','#f59e0b','#10b981','#8b5cf6','#ec4899','#06b6d4','#f97316','#6366f1','#14b8a6'];

type Period = '1m' | '3m' | '6m' | '1y';

export default function Reports() {
  const [period, setPeriod] = useState<Period>('1m');

  const { data: txnData } = useQuery({
    queryKey: ['transactions', { page: 1, page_size: 5000 }],
    queryFn: () => transactionsApi.list({ page: 1, page_size: 5000 }),
  });
  const { data: detData } = useQuery({
    queryKey: ['detection', {}],
    queryFn: () => detectionApi.list({}),
  });

  const transactions: Transaction[] = txnData?.data?.items ?? [];
  const detections = detData?.data ?? [];

  // Filter by period
  const now = new Date();
  const periodDays = { '1m': 30, '3m': 90, '6m': 180, '1y': 365 }[period];
  const cutoff = new Date(now.getTime() - periodDays * 86400000).toISOString();

  const filtered = useMemo(
    () => transactions.filter((t) => t.transaction_date >= cutoff),
    [transactions, cutoff],
  );

  // Monthly trend
  const monthlyTrend = useMemo(() => {
    const byMonth: Record<string, { expense: number; income: number }> = {};
    filtered.forEach((t) => {
      const m = t.transaction_date.slice(0, 7);
      if (!byMonth[m]) byMonth[m] = { expense: 0, income: 0 };
      if (t.type === 'expense') byMonth[m].expense += t.amount;
      else byMonth[m].income += t.amount;
    });
    return Object.entries(byMonth).sort().map(([month, d]) => ({
      month,
      支出: Math.round(d.expense),
      收入: Math.round(d.income),
    }));
  }, [filtered]);

  // Category breakdown
  const categoryBreakdown = useMemo(() => {
    const byCat: Record<string, number> = {};
    filtered.filter((t) => t.type === 'expense').forEach((t) => {
      const k = `cat_${t.category_id || 'unknown'}`;
      byCat[k] = (byCat[k] || 0) + t.amount;
    });
    return Object.entries(byCat)
      .map(([name, value]) => ({ name: name === 'cat_unknown' ? '未分类' : name, value: Math.round(value) }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [filtered]);

  // Detection summary
  const detectionSummary = useMemo(() => {
    const high = detections.filter((d: any) => d.severity === 'high').length;
    const medium = detections.filter((d: any) => d.severity === 'medium').length;
    const low = detections.filter((d: any) => d.severity === 'low').length;
    return [
      { name: '高危', value: high, color: '#ef4444' },
      { name: '中危', value: medium, color: '#f59e0b' },
      { name: '低危', value: low, color: '#10b981' },
    ];
  }, [detections]);

  const totalExpense = filtered.reduce((s, t) => s + (t.type === 'expense' ? t.amount : 0), 0);
  const totalIncome = filtered.reduce((s, t) => s + (t.type === 'income' ? t.amount : 0), 0);
  const avgDaily = Math.round(totalExpense / Math.max(periodDays, 1));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">分析报表</h2>
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1">
          {([
            { k: '1m' as Period, label: '近1月' },
            { k: '3m' as Period, label: '近3月' },
            { k: '6m' as Period, label: '近6月' },
            { k: '1y' as Period, label: '近1年' },
          ]).map(({ k, label }) => (
            <button key={k} onClick={() => setPeriod(k)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                period === k ? 'bg-white shadow-sm font-medium' : 'text-slate-500 hover:text-slate-700'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {[
          { title: '总支出', value: `¥${totalExpense.toLocaleString()}`, color: 'text-red-500' },
          { title: '总收入', value: `¥${totalIncome.toLocaleString()}`, color: 'text-green-500' },
          { title: '日均支出', value: `¥${avgDaily.toLocaleString()}`, color: 'text-slate-700' },
          { title: '异常总数', value: String(detections.length), color: 'text-orange-500' },
        ].map((c) => (
          <div key={c.title} className="bg-white rounded-xl p-4 shadow-sm border">
            <span className="text-sm text-slate-500">{c.title}</span>
            <p className={`text-2xl font-bold ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly trend */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">月度收支趋势</h3>
          {monthlyTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="支出" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="收入" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-center py-12">暂无数据</p>}
        </div>

        {/* Category breakdown */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">支出分类 TOP8</h3>
          {categoryBreakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={categoryBreakdown} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100}>
                  {categoryBreakdown.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-center py-12">暂无数据</p>}
        </div>

        {/* Daily trend */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">每日支出趋势</h3>
          {filtered.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={
                (() => {
                  const byDay: Record<string, number> = {};
                  filtered.filter((t) => t.type === 'expense').forEach((t) => {
                    const d = t.transaction_date.slice(0, 10);
                    byDay[d] = (byDay[d] || 0) + t.amount;
                  });
                  return Object.entries(byDay).sort().slice(-60).map(([date, amount]) => ({ date, amount: Math.round(amount) }));
                })()
              }>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-center py-12">暂无数据</p>}
        </div>

        {/* Detection summary */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">异常检测概览</h3>
          {detections.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={detectionSummary} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100}>
                  {detectionSummary.map((d) => <Cell key={d.name} fill={d.color} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-center py-12">暂无异常数据</p>}
        </div>
      </div>
    </div>
  );
}
