import { Sidebar } from './Sidebar';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

const links = [
  { to: '/dashboard', label: '仪表盘', icon: '📊' },
  { to: '/transactions', label: '交易记录', icon: '📋' },
  { to: '/import', label: '导入数据', icon: '📥' },
  { to: '/detection', label: '异常检测', icon: '🔍' },
  { to: '/reports', label: '分析报表', icon: '📈' },
  { to: '/budget', label: '预算管理', icon: '💰' },
  { to: '/chat', label: 'AI 对话', icon: '🤖' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export function AppLayout({ children }: { children: ReactNode }) {
  useWebSocket();
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      {/* Mobile drawer overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
          <aside className="relative w-60 bg-slate-900 text-white p-4 z-50">
            <h1 className="text-xl font-bold mb-8">FinWatch</h1>
            <nav className="flex flex-col gap-1">
              {links.map(({ to, label, icon }) => (
                <a key={to} href={to} onClick={() => setSidebarOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800">
                  <span>{icon}</span><span>{label}</span>
                </a>
              ))}
            </nav>
          </aside>
        </div>
      )}
      <div className="flex-1 flex flex-col">
        <header className="lg:hidden flex items-center h-14 px-4 border-b bg-white">
          <button onClick={toggleSidebar} className="p-1 mr-3">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
          </button>
          <span className="font-semibold">FinWatch</span>
        </header>
        <main className="flex-1 p-4 md:p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
