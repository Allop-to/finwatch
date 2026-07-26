import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { transactionsApi } from '@/api/client';
import type { Transaction } from '@/types';

export default function Transactions() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['transactions', { page, search }],
    queryFn: () => transactionsApi.list({ page, page_size: 20, search: search || undefined }),
  });
  const items: Transaction[] = data?.data?.items ?? [];
  const total = data?.data?.total ?? 0;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">交易记录</h2>
      <input
        placeholder="搜索商户或备注..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        className="w-full max-w-md px-3 py-2 border rounded-lg text-sm"
      />
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left p-3">日期</th><th className="text-left p-3">商户</th>
              <th className="text-right p-3">金额</th><th className="text-center p-3">来源</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id} className="border-b hover:bg-slate-50">
                <td className="p-3">{t.transaction_date.slice(0, 10)}</td>
                <td className="p-3">{t.merchant || t.description || '--'}</td>
                <td className={`p-3 text-right font-medium ${t.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                  {t.type === 'income' ? '+' : '-'}¥{t.amount.toFixed(2)}
                </td>
                <td className="p-3 text-center">
                  <span className={`px-2 py-0.5 rounded text-xs ${t.source === 'import' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>{t.source}</span>
                </td>
              </tr>
            ))}
            {!isLoading && items.length === 0 && (
              <tr><td colSpan={4} className="p-6 text-center text-slate-400">暂无交易记录</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-500">共 {total} 条</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50">上一页</button>
          <button disabled={page * 20 >= total} onClick={() => setPage((p) => p + 1)}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50">下一页</button>
        </div>
      </div>
    </div>
  );
}
