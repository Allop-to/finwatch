import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

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

export function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-60 bg-slate-900 text-white min-h-screen p-4">
      <h1 className="text-xl font-bold mb-8 px-3">FinWatch</h1>
      <nav className="flex flex-col gap-1">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to} to={to}
            className={({ isActive }) => cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
              isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
            )}
          >
            <span>{icon}</span><span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
