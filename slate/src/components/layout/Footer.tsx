import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-[#E5E5EA] bg-[#F5F5F7]/50">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Product</h4>
            <ul className="space-y-2.5">
              <li><Link href="#features" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Features</Link></li>
              <li><Link href="#pricing" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Pricing</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Templates</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">API</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Company</h4>
            <ul className="space-y-2.5">
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">About</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Blog</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Careers</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Contact</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Resources</h4>
            <ul className="space-y-2.5">
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Help Center</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Documentation</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Status</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Legal</h4>
            <ul className="space-y-2.5">
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Privacy</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Terms</Link></li>
              <li><Link href="#" className="text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors">Security</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-[#E5E5EA] flex items-center justify-between">
          <p className="text-sm text-[#AEAEB2]">
            &copy; {new Date().getFullYear()} Slate, a GEA Technologies company. All rights reserved.
          </p>
          <p className="text-xs text-[#AEAEB2]">
            Made with care in San Francisco.
          </p>
        </div>
      </div>
    </footer>
  );
}
