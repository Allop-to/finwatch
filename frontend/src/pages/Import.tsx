import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importsApi, transactionsApi } from '@/api/client';
import type { ImportResult } from '@/types';

export default function Import() {
  const [mode, setMode] = useState<'file' | 'manual'>('file');
  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-2xl font-bold">导入数据</h2>

      {/* Mode toggle */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
        {[
          { k: 'file' as const, label: '📁 文件导入' },
          { k: 'manual' as const, label: '✏️ 手动录入' },
        ].map(({ k, label }) => (
          <button key={k} onClick={() => setMode(k)}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              mode === k ? 'bg-white shadow-sm font-medium' : 'text-slate-500 hover:text-slate-700'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {mode === 'file' ? <FileImport /> : <ManualEntry />}
    </div>
  );
}

/* ───── File Import ───── */
function FileImport() {
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState('alipay');
  const [result, setResult] = useState<ImportResult | null>(null);
  const qc = useQueryClient();

  const uploadMut = useMutation({
    mutationFn: () => importsApi.upload(file!, sourceType),
    onSuccess: (res) => { setResult(res.data); qc.invalidateQueries({ queryKey: ['transactions'] }); },
  });

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) setFile(f);
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
        <h3 className="font-semibold">① 选择数据来源</h3>
        <div className="flex gap-3">
          {[{ k: 'alipay', label: '支付宝' }, { k: 'wechat', label: '微信' }].map(({ k, label }) => (
            <button key={k} onClick={() => setSourceType(k)}
              className={`px-4 py-2 rounded-lg text-sm ${sourceType === k ? 'bg-slate-900 text-white' : 'border hover:bg-slate-50'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
        <h3 className="font-semibold">② 上传文件</h3>
        <div className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
          onDrop={onDrop} onDragOver={(e) => e.preventDefault()}
          onClick={() => document.getElementById('fileInput')?.click()}>
          <p className="text-slate-500">{file ? file.name : '拖拽 CSV 到此处，或点击选择'}</p>
          <input id="fileInput" type="file" accept=".csv" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        <button onClick={() => uploadMut.mutate()} disabled={!file || uploadMut.isPending}
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm disabled:opacity-50">
          {uploadMut.isPending ? '导入中...' : '开始导入'}
        </button>
      </div>
      {result && (
        <div className="bg-white rounded-xl p-6 shadow-sm border space-y-2">
          <h3 className="font-semibold">③ 导入完成</h3>
          <p className="text-green-600">✅ 成功导入 {result.new_count} 条，跳过 {result.skipped_count} 条重复</p>
        </div>
      )}
      {uploadMut.isError && <p className="text-red-500">❌ 导入失败，请检查文件格式</p>}
    </div>
  );
}

/* ───── Manual Entry ───── */
function ManualEntry() {
  const qc = useQueryClient();
  const [amount, setAmount] = useState('');
  const [txnType, setTxnType] = useState('expense');
  const [merchant, setMerchant] = useState('');
  const [desc, setDesc] = useState('');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 16));
  const [paymentMethod, setPaymentMethod] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [batchMode, setBatchMode] = useState(false);
  const [batchText, setBatchText] = useState('');

  const createMut = useMutation({
    mutationFn: (data: any) => transactionsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] });
      setResult('✅ 录入成功');
      if (!batchMode) { setAmount(''); setMerchant(''); setDesc(''); }
    },
    onError: () => setResult('❌ 录入失败'),
  });

  const handleSubmit = () => {
    if (!amount || !date) return;
    createMut.mutate({
      amount: parseFloat(amount),
      type: txnType,
      transaction_date: new Date(date).toISOString(),
      merchant: merchant || null,
      description: desc || null,
      payment_method: paymentMethod || null,
      source: 'manual',
    });
  };

  const handleBatchSubmit = () => {
    const lines = batchText.trim().split('\n').filter(Boolean);
    let count = 0;
    lines.forEach((line) => {
      const parts = line.split(/[\s,]+/);
      if (parts.length >= 2) {
        const amt = parseFloat(parts[0]);
        const m = parts.slice(1).join(' ') || null;
        if (!isNaN(amt)) {
          createMut.mutate({
            amount: Math.abs(amt),
            type: amt >= 0 ? 'income' : 'expense',
            transaction_date: new Date().toISOString(),
            merchant: m,
            source: 'manual',
          });
          count++;
        }
      }
    });
    setResult(`✅ 批量录入 ${count} 条`);
    setBatchText('');
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{batchMode ? '批量录入' : '手动录入'}</h3>
          <button onClick={() => setBatchMode(!batchMode)}
            className="text-sm text-blue-600 hover:underline">
            {batchMode ? '单笔录入' : '切换到批量录入'}
          </button>
        </div>

        {!batchMode ? (
          <>
            <div className="flex gap-3">
              <select value={txnType} onChange={(e) => setTxnType(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm">
                <option value="expense">支出</option>
                <option value="income">收入</option>
                <option value="transfer">转账</option>
              </select>
              <input placeholder="金额" value={amount} onChange={(e) => setAmount(e.target.value)}
                className="flex-1 px-3 py-2 border rounded-lg text-sm" type="number" step="0.01" />
            </div>
            <input placeholder="商户名称" value={merchant} onChange={(e) => setMerchant(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm" />
            <input placeholder="备注（可选）" value={desc} onChange={(e) => setDesc(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm" />
            <div className="flex gap-3">
              <input type="datetime-local" value={date} onChange={(e) => setDate(e.target.value)}
                className="flex-1 px-3 py-2 border rounded-lg text-sm" />
              <input placeholder="支付方式" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}
                className="w-32 px-3 py-2 border rounded-lg text-sm" />
            </div>
            <button onClick={handleSubmit} disabled={createMut.isPending || !amount || !date}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm disabled:opacity-50">
              {createMut.isPending ? '保存中...' : '录入'}
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-slate-500">每行一条，格式：<code>金额 商户名</code>（支出为负数）</p>
            <textarea value={batchText} onChange={(e) => setBatchText(e.target.value)}
              placeholder={"42.50 星巴克咖啡\n-28.00 滴滴打车\n15000 工资收入"}
              className="w-full h-32 px-3 py-2 border rounded-lg text-sm font-mono" />
            <button onClick={handleBatchSubmit} disabled={!batchText.trim()}
              className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm disabled:opacity-50">
              批量录入
            </button>
          </>
        )}

        {result && <p className={`text-sm ${result.startsWith('✅') ? 'text-green-600' : 'text-red-500'}`}>{result}</p>}
      </div>
    </div>
  );
}
