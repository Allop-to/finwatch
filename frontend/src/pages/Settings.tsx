import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { categoriesApi, api } from '@/api/client';
import type { Category } from '@/types';

interface Rule {
  id: number; name: string; condition: Record<string, any>;
  is_hard_rule: boolean; is_enabled: boolean;
}

interface DataStats {
  transactions: number; detections: number; budgets: number;
  categories: number; db_size_kb: number;
}

export default function Settings() {
  const [tab, setTab] = useState<'categories' | 'rules' | 'data'>('categories');
  const qc = useQueryClient();

  return (
    <div className="space-y-4 max-w-2xl">
      <h2 className="text-2xl font-bold">设置</h2>
      <div className="flex gap-2 border-b pb-2">
        {[
          { key: 'categories' as const, label: '分类管理' },
          { key: 'rules' as const, label: '检测规则' },
          { key: 'data' as const, label: '数据管理' },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm rounded-t-lg ${tab === key ? 'bg-white border-b-2 border-blue-500 font-medium' : 'text-slate-500 hover:text-slate-700'}`}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'categories' && <CategoriesTab />}
      {tab === 'rules' && <RulesTab />}
      {tab === 'data' && <DataTab />}
    </div>
  );
}

/* ───── Categories Tab ───── */
function CategoriesTab() {
  const [newCatName, setNewCatName] = useState('');
  const qc = useQueryClient();
  const { data: catsData } = useQuery({ queryKey: ['categories'], queryFn: () => categoriesApi.list() });
  const createCatMut = useMutation({
    mutationFn: () => categoriesApi.create({ name: newCatName }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['categories'] }); setNewCatName(''); },
  });
  const deleteCatMut = useMutation({
    mutationFn: (id: number) => categoriesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  });

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input placeholder="新分类名称" value={newCatName} onChange={(e) => setNewCatName(e.target.value)}
          className="flex-1 px-3 py-2 border rounded-lg text-sm" />
        <button onClick={() => createCatMut.mutate()} disabled={!newCatName || createCatMut.isPending}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm disabled:opacity-50">添加</button>
      </div>
      <div className="space-y-1">
        {(catsData?.data ?? []).map((cat: Category) => (
          <div key={cat.id} className="flex items-center justify-between bg-white rounded-lg p-3 border">
            <div className="flex items-center gap-2">
              <span>{cat.icon || '📁'}</span><span>{cat.name}</span>
              {cat.is_system && <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded text-xs">系统</span>}
            </div>
            {!cat.is_system && (
              <button onClick={() => deleteCatMut.mutate(cat.id)} className="text-red-500 text-sm">删除</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ───── Rules Tab ───── */
function RulesTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['rules'], queryFn: () => api.get('/rules'),
  });
  const rules: Rule[] = data?.data ?? [];

  const toggleMut = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      api.put(`/rules/${id}`, { is_enabled: enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => api.delete(`/rules/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  });
  const seedMut = useMutation({
    mutationFn: () => api.post('/rules/seed-defaults'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  });

  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');
  const [newField, setNewField] = useState('amount');
  const [newOp, setNewOp] = useState('>');
  const [newVal, setNewVal] = useState('');
  const [newHard, setNewHard] = useState(false);

  const createMut = useMutation({
    mutationFn: () => api.post('/rules', {
      name: newName,
      condition: { field: newField, operator: newOp, value: parseFloat(newVal) || newVal },
      is_hard_rule: newHard,
      is_enabled: true,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rules'] }); setShowAdd(false); setNewName(''); setNewVal(''); },
  });

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button onClick={() => setShowAdd(!showAdd)}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm">{showAdd ? '取消' : '+ 新建规则'}</button>
        {rules.length === 0 && (
          <button onClick={() => seedMut.mutate()} disabled={seedMut.isPending}
            className="px-4 py-2 border rounded-lg text-sm hover:bg-slate-50">初始化默认规则</button>
        )}
      </div>

      {showAdd && (
        <div className="bg-white rounded-xl p-4 border space-y-3">
          <input placeholder="规则名称" value={newName} onChange={(e) => setNewName(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm" />
          <div className="flex gap-2">
            <select value={newField} onChange={(e) => setNewField(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm">
              <option value="amount">金额</option>
              <option value="hour">时间(小时)</option>
              <option value="daily_count">日消费笔数</option>
            </select>
            <select value={newOp} onChange={(e) => setNewOp(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm">
              <option value=">">&gt;</option>
              <option value="<">&lt;</option>
              <option value=">=">&gt;=</option>
              <option value="in">属于</option>
            </select>
            <input placeholder="值" value={newVal} onChange={(e) => setNewVal(e.target.value)}
              className="w-24 px-3 py-2 border rounded-lg text-sm" />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={newHard} onChange={(e) => setNewHard(e.target.checked)} />
            硬规则（否决权：命中即高危）
          </label>
          <button onClick={() => createMut.mutate()} disabled={createMut.isPending || !newName || !newVal}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50">保存</button>
        </div>
      )}

      {isLoading && <p className="text-slate-400 text-sm">加载中...</p>}

      <div className="space-y-2">
        {rules.map((r) => (
          <div key={r.id} className="flex items-center justify-between bg-white rounded-lg p-3 border">
            <div className="flex items-center gap-3">
              <button
                onClick={() => toggleMut.mutate({ id: r.id, enabled: !r.is_enabled })}
                className={`w-10 h-5 rounded-full transition-colors relative ${r.is_enabled ? 'bg-green-500' : 'bg-gray-300'}`}>
                <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${r.is_enabled ? 'left-5' : 'left-0.5'}`} />
              </button>
              <div>
                <span className="text-sm font-medium">{r.name}</span>
                <span className="ml-2 text-xs text-slate-400">
                  {r.condition.field} {r.condition.operator} {JSON.stringify(r.condition.value)}
                </span>
              </div>
              {r.is_hard_rule && <span className="px-1.5 py-0.5 bg-red-100 text-red-600 rounded text-xs">硬规则</span>}
            </div>
            <button onClick={() => deleteMut.mutate(r.id)} className="text-red-400 text-sm hover:text-red-600">删除</button>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ───── Data Tab ───── */
function DataTab() {
  const qc = useQueryClient();
  const { data: stats } = useQuery({
    queryKey: ['data-stats'], queryFn: () => api.get('/rules/data/stats'),
  });
  const s: DataStats | undefined = stats?.data;

  const exportMut = useMutation({
    mutationFn: async () => {
      const resp = await api.get('/rules/data/export', { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement('a'); a.href = url;
      a.download = `finwatch_export_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click(); URL.revokeObjectURL(url);
    },
  });
  const clearDetectionsMut = useMutation({
    mutationFn: () => api.post('/rules/data/clear-detections'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['data-stats'] }),
  });
  const clearAllMut = useMutation({
    mutationFn: () => api.post('/rules/data/clear-all'),
    onSuccess: () => { qc.invalidateQueries(); qc.invalidateQueries({ queryKey: ['data-stats'] }); },
  });

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="bg-white rounded-xl p-4 border">
        <h3 className="font-semibold mb-3">数据库概览</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-slate-500">交易记录</span><p className="font-bold text-lg">{s?.transactions ?? '-'}</p></div>
          <div><span className="text-slate-500">检测结果</span><p className="font-bold text-lg">{s?.detections ?? '-'}</p></div>
          <div><span className="text-slate-500">预算数量</span><p className="font-bold text-lg">{s?.budgets ?? '-'}</p></div>
          <div><span className="text-slate-500">数据库大小</span><p className="font-bold text-lg">{s?.db_size_kb ?? '-'} KB</p></div>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-xl p-4 border space-y-3">
        <h3 className="font-semibold">数据操作</h3>

        <button onClick={() => exportMut.mutate()} disabled={exportMut.isPending}
          className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors">
          📥 导出 CSV
        </button>

        <button onClick={() => { if (confirm('确认清空所有检测结果？')) clearDetectionsMut.mutate(); }}
          disabled={clearDetectionsMut.isPending}
          className="w-full px-4 py-2.5 border border-orange-300 text-orange-600 rounded-lg text-sm hover:bg-orange-50 transition-colors">
          🗑️ 清空检测结果
        </button>

        <button onClick={() => { if (confirm('⚠️ 确认清空所有数据（交易/检测/预算）？此操作不可恢复！')) clearAllMut.mutate(); }}
          disabled={clearAllMut.isPending}
          className="w-full px-4 py-2.5 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50 transition-colors">
          ⚠️ 清空全部数据
        </button>
      </div>
    </div>
  );
}
