'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FileText,
  BookTemplate,
  User,
  Coins,
  Settings,
  Zap,
  LogOut,
} from 'lucide-react';
import { useCreditStore } from '@/stores/creditStore';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/fill', label: 'Fill a Form', icon: FileText },
  { href: '/templates', label: 'Templates', icon: BookTemplate },
  { href: '/profiles', label: 'Data Profiles', icon: User },
  { href: '/credits', label: 'Credits', icon: Coins },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const balance = useCreditStore((s) => s.balance);

  return (
    <aside className="w-60 h-screen bg-[#F5F5F7]/50 border-r border-[#E5E5EA] flex flex-col fixed left-0 top-0">
      <div className="h-14 flex items-center px-5 border-b border-[#E5E5EA]/60">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-7 h-7 bg-[#1D1D1F] rounded-lg flex items-center justify-center">
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-[#1D1D1F]">
            Slate
          </span>
        </Link>
      </div>

      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium
                    transition-all duration-150
                    ${isActive
                      ? 'bg-white text-[#1D1D1F] shadow-sm border border-[#E5E5EA]/60'
                      : 'text-[#86868B] hover:bg-white/60 hover:text-[#1D1D1F]'
                    }
                  `}
                >
                  <Icon size={18} strokeWidth={isActive ? 2 : 1.5} />
                  {item.label}
                  {item.href === '/credits' && (
                    <span className="ml-auto text-xs font-semibold text-[#5856D6] bg-[#5856D6]/10 px-2 py-0.5 rounded-full">
                      {balance}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-3 border-t border-[#E5E5EA]/60">
        <button className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-[#86868B] hover:bg-white/60 hover:text-[#1D1D1F] transition-all duration-150 w-full cursor-pointer">
          <LogOut size={18} strokeWidth={1.5} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
