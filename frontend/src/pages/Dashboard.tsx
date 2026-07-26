import { useQuery } from '@tanstack/react-query';
import { transactionsApi, detectionApi, budgetApi } from '@/api/client';
import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import type { Transaction } from '@/types';

const COLORS = ['#3b82f6','#ef4444','#f59e0b','#10b981','#8b5cf6','#ec4899','#06b6d4','#f97316','#6366f1','#14b8a6'];

function StatCard({ title, value, color }: { title: string; value: string; color: string }) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border">
      <span className="text-sm text-slate-500">{title}</span>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const { data: txnData } = useQuery({
    queryKey: ['transactions', { page: 1, page_size: 1000 }],
    queryFn: () => transactionsApi.list({ page: 1, page_size: 1000 }),
  });
  const { data: detections } = useQuery({
    queryKey: ['detection'], queryFn: () => detectionApi.list(),
  });
  const { data: budgets } = useQuery({
    queryKey: ['budgets'], queryFn: () => budgetApi.list(),
  });

  const transactions: Transaction[] = txnData?.data?.items ?? [];
  const monthExpense = useMemo(
    () => transactions.filter((t) => t.type === 'expense').reduce((s, t) => s + t.amount, 0),
    [transactions],
  );
  const unreadAlerts = detections?.data?.filter((d: any) => !d.is_read).length ?? 0;
  const totalBudget = budgets?.data?.[0]?.amount_limit ?? 0;

  const trendData = useMemo(() => {
    const byDate: Record<string, number> = {};
    transactions.filter((t) => t.type === 'expense').forEach((t) => {
      const day = t.transaction_date.slice(0, 10);
      byDate[day] = (byDate[day] || 0) + t.amount;
    });
    return Object.entries(byDate).sort().slice(-30).map(([date, amount]) => ({ date, amount }));
  }, [transactions]);

  const pieData = useMemo(() => {
    const byCat: Record<string, number> = {};
    transactions.filter((t) => t.type === 'expense').forEach((t) => {
      const k = t.category_id ? `cat_${t.category_id}` : '未分类';
      byCat[k] = (byCat[k] || 0) + t.amount;
    });
    return Object.entries(byCat).map(([name, value]) => ({ name, value }));
  }, [transactions]);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">仪表盘</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="本月支出" value={`¥${monthExpense.toLocaleString()}`} color="text-red-500" />
        <StatCard title="环比变化" value="--" color="text-orange-500" />
        <StatCard title="预算剩余" value={`¥${(totalBudget - monthExpense).toLocaleString()}`} color="text-green-500" />
        <StatCard title="未读异常" value={String(unreadAlerts)} color={unreadAlerts > 0 ? 'text-red-500' : 'text-gray-400'} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">近30天支出趋势</h3>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400">暂无数据</p>}
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="font-semibold mb-4">支出分类占比</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip /><Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400">暂无数据</p>}
        </div>
      </div>
    </div>
  );
}
