import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { detectionApi } from '@/api/client';
import type { DetectionResult } from '@/types';

const sevBadge = (s: string) => {
  if (s === 'high') return { cls: 'bg-red-100 text-red-700', label: '🔴 高' };
  if (s === 'medium') return { cls: 'bg-yellow-100 text-yellow-700', label: '🟡 中' };
  return { cls: 'bg-green-100 text-green-700', label: '🟢 低' };
};

export default function Detection() {
  const [severity, setSeverity] = useState('');
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ['detection', { severity: severity || undefined }],
    queryFn: () => detectionApi.list({ severity: severity || undefined }),
  });
  const runMut = useMutation({
    mutationFn: () => detectionApi.run(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['detection'] }),
  });
  const items: DetectionResult[] = data?.data ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">异常检测</h2>
        <button onClick={() => runMut.mutate()} disabled={runMut.isPending}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm disabled:opacity-50">
          {runMut.isPending ? '检测中...' : '立即检测'}
        </button>
      </div>
      <select value={severity} onChange={(e) => setSeverity(e.target.value)}
        className="px-3 py-2 border rounded-lg text-sm w-40">
        <option value="">全部等级</option>
        <option value="high">高危</option>
        <option value="medium">中危</option>
        <option value="low">低危</option>
      </select>
      <div className="space-y-3">
        {items.map((r) => {
          const b = sevBadge(r.severity);
          return (
            <div key={r.id} className="bg-white rounded-xl p-4 shadow-sm border">
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${b.cls}`}>{b.label}</span>
                <span className="text-xs text-slate-400">{r.created_at.slice(0, 10)}</span>
              </div>
              <p className="text-sm text-slate-600">{r.reason?.[0]?.detail ?? '检测到异常消费模式'}</p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-slate-400">{r.detector_type}</span>
                <span className="text-xs font-mono">分数: {r.anomaly_score.toFixed(3)}</span>
              </div>
            </div>
          );
        })}
        {items.length === 0 && <p className="text-center text-slate-400 py-12">暂无异常检测结果</p>}
      </div>
    </div>
  );
}
