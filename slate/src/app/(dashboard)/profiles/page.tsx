'use client';

import { useState } from 'react';
import { Plus, User, Pencil, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { DEFAULT_PROFILE_FIELDS } from '@/types/profile';

export default function ProfilesPage() {
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Data Profiles</h1>
          <p className="text-sm text-[#86868B] mt-1">
            Save your information to auto-fill forms faster.
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus size={16} />
          New Profile
        </Button>
      </div>

      {/* Empty State */}
      <Card className="py-16 text-center">
        <div className="w-14 h-14 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mx-auto">
          <User size={28} className="text-[#AEAEB2]" />
        </div>
        <h3 className="text-base font-semibold text-[#1D1D1F] mt-5">No profiles yet</h3>
        <p className="text-sm text-[#86868B] mt-2 max-w-sm mx-auto">
          Create a data profile with your name, address, and other details to drag onto form fields.
        </p>
        <Button
          variant="secondary"
          size="sm"
          className="mt-5"
          onClick={() => setShowCreate(true)}
        >
          Create Your First Profile
        </Button>
      </Card>

      {/* Create Profile Modal */}
      <Modal
        isOpen={showCreate}
        onClose={() => setShowCreate(false)}
        title="New Data Profile"
        size="lg"
      >
        <div className="space-y-4">
          <Input label="Profile Name" placeholder='e.g., "Personal", "Business", "Client - Acme"' />
          <div className="border-t border-[#E5E5EA] pt-4 mt-4">
            <p className="text-sm font-medium text-[#1D1D1F] mb-3">Common Fields</p>
            <div className="grid grid-cols-2 gap-3">
              {DEFAULT_PROFILE_FIELDS.slice(0, 10).map((field) => (
                <Input
                  key={field}
                  label={field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  placeholder={`Enter ${field.replace(/_/g, ' ')}`}
                />
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-[#E5E5EA]">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button>Save Profile</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
