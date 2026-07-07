import Link from 'next/link';
import { Zap } from 'lucide-react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#F2F4F7] flex flex-col items-center justify-center p-6">
      <Link href="/" className="flex items-center gap-2 mb-10">
        <div className="w-8 h-8 bg-[#1B1D24] rounded-lg flex items-center justify-center">
          <Zap size={16} className="text-white" />
        </div>
        <span className="text-xl font-semibold tracking-tight text-[#1B1D24]">
          Slate
        </span>
      </Link>
      {children}
    </div>
  );
}
