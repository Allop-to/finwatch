import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { budgetApi } from '@/api/client';
import type { Budget } from '@/types';

export default function Budget() {
  const [showForm, setShowForm] = useState(false);
  const [amount, setAmount] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const qc = useQueryClient();

  const { data } = useQuery({ queryKey: ['budgets'], queryFn: () => budgetApi.list() });
  const createMut = useMutation({
    mutationFn: () => budgetApi.create({ amount_limit: +amount, start_date: start, end_date: end, period: 'monthly' }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['budgets'] }); setShowForm(false); setAmount(''); setStart(''); setEnd(''); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => budgetApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['budgets'] }),
  });

  const items: Budget[] = data?.data ?? [];

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">预算管理</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm">{showForm ? '取消' : '+ 新建预算'}</button>
      </div>
      {showForm && (
        <div className="bg-white rounded-xl p-4 shadow-sm border space-y-3">
          <input placeholder="预算金额" value={amount} onChange={(e) => setAmount(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm" type="number" />
          <div className="flex gap-3">
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)}
              className="flex-1 px-3 py-2 border rounded-lg text-sm" />
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)}
              className="flex-1 px-3 py-2 border rounded-lg text-sm" />
          </div>
          <button onClick={() => createMut.mutate()} disabled={createMut.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50">保存</button>
        </div>
      )}
      <div className="space-y-3">
        {items.map((b) => (
          <div key={b.id} className="bg-white rounded-xl p-4 shadow-sm border">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">总预算 ¥{b.amount_limit.toLocaleString()}</span>
              <button onClick={() => deleteMut.mutate(b.id)} className="text-red-500 text-sm">删除</button>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div className={`h-3 rounded-full transition-all ${b.progress_pct > 80 ? 'bg-red-500' : b.progress_pct > 50 ? 'bg-yellow-500' : 'bg-green-500'}`}
                style={{ width: `${Math.min(b.progress_pct, 100)}%` }} />
            </div>
            <div className="flex justify-between mt-1 text-xs text-slate-500">
              <span>已用 ¥{(b.spent_amount || 0).toLocaleString()}</span>
              <span>{b.progress_pct}%</span>
            </div>
          </div>
        ))}
        {items.length === 0 && <p className="text-center text-slate-400 py-12">暂无预算，点击上方按钮创建</p>}
      </div>
    </div>
  );
}
