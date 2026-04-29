import Link from 'next/link';

const disabledLinkClass = 'text-sm text-[#86868B] opacity-50 cursor-not-allowed';
const activeLinkClass = 'text-sm text-[#86868B] hover:text-[#1D1D1F] transition-colors';

function DisabledLink({ children }: { children: React.ReactNode }) {
  return (
    <a
      href="#"
      aria-disabled="true"
      onClick={(e) => e.preventDefault()}
      className={disabledLinkClass}
    >
      {children}
    </a>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-[#E5E5EA] bg-[#F5F5F7]/50">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Product</h4>
            <ul className="space-y-2.5">
              <li><Link href="#features" className={activeLinkClass}>Features</Link></li>
              <li><Link href="#pricing" className={activeLinkClass}>Pricing</Link></li>
              <li><DisabledLink>Templates</DisabledLink></li>
              <li><DisabledLink>API</DisabledLink></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Company</h4>
            <ul className="space-y-2.5">
              <li><DisabledLink>About</DisabledLink></li>
              <li><DisabledLink>Blog</DisabledLink></li>
              <li><DisabledLink>Careers</DisabledLink></li>
              <li><DisabledLink>Contact</DisabledLink></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Resources</h4>
            <ul className="space-y-2.5">
              <li><DisabledLink>Help Centre</DisabledLink></li>
              <li><DisabledLink>Documentation</DisabledLink></li>
              <li><DisabledLink>Status</DisabledLink></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-4">Legal</h4>
            <ul className="space-y-2.5">
              <li><Link href="/privacy" className={activeLinkClass}>Privacy</Link></li>
              <li><Link href="/terms" className={activeLinkClass}>Terms</Link></li>
              <li><DisabledLink>Security</DisabledLink></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-[#E5E5EA] flex items-center justify-between">
          <p className="text-sm text-[#AEAEB2]">
            &copy; {new Date().getFullYear()} Slate, a GEA Technologies company. All rights reserved.
          </p>
          <p className="text-xs text-[#AEAEB2]">
            Made with care in Melbourne, Australia.
          </p>
        </div>
      </div>
    </footer>
  );
}
