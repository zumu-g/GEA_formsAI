'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  FileText,
  Wand2,
  BookTemplate,
  User,
  Coins,
  Settings,
  Zap,
  LogOut,
  Clock,
  Sparkles,
} from 'lucide-react';
import { useCreditStore } from '@/stores/creditStore';
import { createClient } from '@/lib/supabase/client';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/fill', label: 'Fill a Form', icon: FileText },
  { href: '/fill/smart', label: 'Smart Fill', icon: Sparkles },
  { href: '/fill/history', label: 'Fill History', icon: Clock },
  { href: '/skills', label: 'Skills', icon: Wand2 },
  { href: '/templates', label: 'Templates', icon: BookTemplate },
  { href: '/profiles', label: 'Data Profiles', icon: User },
  { href: '/credits', label: 'Credits', icon: Coins },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const balance = useCreditStore((s) => s.balance);

  const handleSignOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  return (
    <aside className="w-60 h-screen bg-[#F2F4F7]/50 border-r border-[#E2E4EA] flex flex-col fixed left-0 top-0">
      <div className="h-14 flex items-center px-5 border-b border-[#E2E4EA]/60">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-7 h-7 bg-[#1B1D24] rounded-lg flex items-center justify-center">
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-[#1B1D24]">
            Slate
          </span>
        </Link>
      </div>

      <nav className="flex-1 py-4 px-3">
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            // Exact match, or starts with item.href + '/' but is NOT a more-specific nav item
            const isActive =
              pathname === item.href ||
              (pathname?.startsWith(item.href + '/') &&
                !navItems.some(
                  (other) =>
                    other.href !== item.href &&
                    other.href.startsWith(item.href + '/') &&
                    (pathname === other.href || pathname?.startsWith(other.href + '/'))
                ));
            const Icon = item.icon;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium
                    transition-all duration-150
                    ${isActive
                      ? 'bg-white text-[#1B1D24] shadow-sm border border-[#E2E4EA]/60'
                      : 'text-[#767A85] hover:bg-white/60 hover:text-[#1B1D24]'
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

      <div className="p-3 border-t border-[#E2E4EA]/60">
        <button
          onClick={handleSignOut}
          className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-[#767A85] hover:bg-white/60 hover:text-[#1B1D24] transition-all duration-150 w-full cursor-pointer"
        >
          <LogOut size={18} strokeWidth={1.5} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
