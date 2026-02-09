'use client';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

export default function SettingsPage() {
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-[#1D1D1F] mb-8">Settings</h1>

      <div className="space-y-8">
        {/* Profile */}
        <Card>
          <h2 className="text-base font-semibold text-[#1D1D1F] mb-4">Profile</h2>
          <div className="space-y-4">
            <Input label="Display Name" placeholder="Jane Doe" />
            <Input label="Email" type="email" placeholder="jane@company.com" disabled />
            <Input label="Company Name" placeholder="Acme Inc." />
          </div>
          <div className="mt-4 flex justify-end">
            <Button size="sm">Save Changes</Button>
          </div>
        </Card>

        {/* Data Retention */}
        <Card>
          <h2 className="text-base font-semibold text-[#1D1D1F] mb-2">Data Retention</h2>
          <p className="text-sm text-[#86868B] mb-4">
            Control how long your uploaded PDFs are stored. Filled forms are available for download for this period.
          </p>
          <select className="h-10 px-3 rounded-xl border border-[#E5E5EA] bg-white text-sm text-[#1D1D1F] w-48">
            <option>7 days</option>
            <option>30 days (default)</option>
            <option>90 days</option>
            <option>1 year</option>
          </select>
        </Card>

        {/* Danger Zone */}
        <Card className="border-[#FF3B30]/20">
          <h2 className="text-base font-semibold text-[#FF3B30] mb-2">Danger Zone</h2>
          <p className="text-sm text-[#86868B] mb-4">
            Permanently delete your account and all associated data. This action cannot be undone.
          </p>
          <Button variant="danger" size="sm">Delete Account</Button>
        </Card>
      </div>
    </div>
  );
}
