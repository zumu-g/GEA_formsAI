'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, User, Pencil, Trash2, Star, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { DataProfile, PROFILE_RESUME_KEYS } from '@/types/profile';

// ---------------------------------------------------------------------------
// Field helpers
// ---------------------------------------------------------------------------

function fieldLabel(field: string): string {
  // Use the friendly label from PROFILE_RESUME_KEYS when available
  if (field in PROFILE_RESUME_KEYS) {
    return PROFILE_RESUME_KEYS[field as keyof typeof PROFILE_RESUME_KEYS];
  }
  return field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-AU', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function filledFieldCount(data: Record<string, string>): number {
  return Object.values(data).filter((v) => v && v.trim().length > 0).length;
}

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

type TabId = 'personal' | 'address' | 'professional' | 'online' | 'resume';

interface TabDef {
  id: TabId;
  label: string;
}

const TABS: TabDef[] = [
  { id: 'personal', label: 'Personal' },
  { id: 'address', label: 'Address' },
  { id: 'professional', label: 'Professional' },
  { id: 'online', label: 'Online' },
  { id: 'resume', label: 'Resume' },
];

// ---------------------------------------------------------------------------
// Inline form field components
// ---------------------------------------------------------------------------

interface FieldInputProps {
  label: string;
  fieldKey: string;
  value: string;
  onChange: (key: string, value: string) => void;
  placeholder?: string;
  type?: 'text' | 'email' | 'tel' | 'url' | 'number';
}

function FieldInput({ label, fieldKey, value, onChange, placeholder, type = 'text' }: FieldInputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-[#1D1D1F]">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        placeholder={placeholder ?? `Enter ${label.toLowerCase()}`}
        className="h-10 px-3 rounded-xl border border-[#E5E5EA] bg-white text-sm text-[#1D1D1F] placeholder:text-[#AEAEB2] transition-all duration-200 hover:border-[#C7C7CC] focus:outline-none focus:ring-2 focus:ring-[#5856D6]/20 focus:border-[#5856D6]"
      />
    </div>
  );
}

interface FieldTextareaProps {
  label: string;
  fieldKey: string;
  value: string;
  onChange: (key: string, value: string) => void;
  placeholder?: string;
  rows?: number;
}

function FieldTextarea({ label, fieldKey, value, onChange, placeholder, rows = 4 }: FieldTextareaProps) {
  return (
    <div className="flex flex-col gap-1.5 col-span-2">
      <label className="text-sm font-medium text-[#1D1D1F]">{label}</label>
      <textarea
        rows={rows}
        value={value}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        placeholder={placeholder ?? `Enter ${label.toLowerCase()}`}
        className="px-3 py-2.5 rounded-xl border border-[#E5E5EA] bg-white text-sm text-[#1D1D1F] placeholder:text-[#AEAEB2] transition-all duration-200 hover:border-[#C7C7CC] focus:outline-none focus:ring-2 focus:ring-[#5856D6]/20 focus:border-[#5856D6] resize-none"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section heading
// ---------------------------------------------------------------------------

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-medium text-[#86868B] uppercase tracking-wide mb-3">
      {children}
    </p>
  );
}

// ---------------------------------------------------------------------------
// Tab panels
// ---------------------------------------------------------------------------

interface TabPanelProps {
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

function PersonalTab({ values, onChange }: TabPanelProps) {
  return (
    <div>
      <SectionHeading>Personal Information</SectionHeading>
      <div className="grid grid-cols-2 gap-3">
        <FieldInput label="Full Name" fieldKey="full_name" value={values.full_name ?? ''} onChange={onChange} placeholder="e.g. Jane Smith" />
        <FieldInput label="Email" fieldKey="email" value={values.email ?? ''} onChange={onChange} type="email" placeholder="e.g. jane@example.com" />
        <FieldInput label="First Name" fieldKey="first_name" value={values.first_name ?? ''} onChange={onChange} placeholder="e.g. Jane" />
        <FieldInput label="Last Name" fieldKey="last_name" value={values.last_name ?? ''} onChange={onChange} placeholder="e.g. Smith" />
        <FieldInput label="Phone" fieldKey="phone" value={values.phone ?? ''} onChange={onChange} type="tel" placeholder="e.g. 0412 345 678" />
        <FieldInput label="Date of Birth" fieldKey="date_of_birth" value={values.date_of_birth ?? ''} onChange={onChange} placeholder="dd/mm/yyyy" />
      </div>
    </div>
  );
}

function AddressTab({ values, onChange }: TabPanelProps) {
  return (
    <div>
      <SectionHeading>Address</SectionHeading>
      <div className="grid grid-cols-2 gap-3">
        <FieldInput label="Address Line 1" fieldKey="address_line_1" value={values.address_line_1 ?? ''} onChange={onChange} placeholder="e.g. 10 Collins Street" />
        <FieldInput label="Address Line 2" fieldKey="address_line_2" value={values.address_line_2 ?? ''} onChange={onChange} placeholder="e.g. Unit 5" />
        <FieldInput label="City / Suburb" fieldKey="city" value={values.city ?? ''} onChange={onChange} placeholder="e.g. Melbourne" />
        <FieldInput label="State" fieldKey="state" value={values.state ?? ''} onChange={onChange} placeholder="e.g. VIC" />
        <FieldInput label="Postcode" fieldKey="zip_code" value={values.zip_code ?? ''} onChange={onChange} placeholder="e.g. 3000" />
        <FieldInput label="Country" fieldKey="country" value={values.country ?? ''} onChange={onChange} placeholder="e.g. Australia" />
      </div>
    </div>
  );
}

function ProfessionalTab({ values, onChange }: TabPanelProps) {
  return (
    <div className="space-y-5">
      <div>
        <SectionHeading>Employment</SectionHeading>
        <div className="grid grid-cols-2 gap-3">
          <FieldInput label="Company Name" fieldKey="company_name" value={values.company_name ?? ''} onChange={onChange} placeholder="e.g. Acme Pty Ltd" />
          <FieldInput label="Job Title" fieldKey="job_title" value={values.job_title ?? ''} onChange={onChange} placeholder="e.g. Senior Engineer" />
          <FieldInput label="Current Employer" fieldKey="current_employer" value={values.current_employer ?? ''} onChange={onChange} placeholder="e.g. Acme Corp" />
          <FieldInput label="Current Role" fieldKey="current_role" value={values.current_role ?? ''} onChange={onChange} placeholder="e.g. Product Manager" />
          <FieldInput label="Years of Experience" fieldKey="years_experience" value={values.years_experience ?? ''} onChange={onChange} type="number" placeholder="e.g. 5" />
        </div>
      </div>

      <div>
        <SectionHeading>Registrations &amp; Licences</SectionHeading>
        <div className="grid grid-cols-2 gap-3">
          <FieldInput label="ABN" fieldKey="abn" value={values.abn ?? ''} onChange={onChange} placeholder="e.g. 12 345 678 901" />
          <FieldInput label="ACN" fieldKey="acn" value={values.acn ?? ''} onChange={onChange} placeholder="e.g. 123 456 789" />
          <FieldInput label="Tax ID / TFN" fieldKey="tax_id" value={values.tax_id ?? ''} onChange={onChange} placeholder="e.g. 123 456 789" />
          <FieldInput label="Licence Number" fieldKey="licence_number" value={values.licence_number ?? ''} onChange={onChange} placeholder="e.g. VIC123456" />
          <FieldInput label="Licence Type" fieldKey="licence_type" value={values.licence_type ?? ''} onChange={onChange} placeholder="e.g. Real Estate Agent" />
        </div>
      </div>
    </div>
  );
}

function OnlineTab({ values, onChange }: TabPanelProps) {
  return (
    <div>
      <SectionHeading>Online Profiles</SectionHeading>
      <div className="grid grid-cols-2 gap-3">
        <FieldInput label="LinkedIn URL" fieldKey="linkedin_url" value={values.linkedin_url ?? ''} onChange={onChange} type="url" placeholder="https://linkedin.com/in/yourname" />
        <FieldInput label="Website / Portfolio" fieldKey="website_url" value={values.website_url ?? ''} onChange={onChange} type="url" placeholder="https://yourwebsite.com" />
      </div>
    </div>
  );
}

function ResumeTab({ values, onChange }: TabPanelProps) {
  return (
    <div className="space-y-5">
      <div>
        <SectionHeading>Qualifications</SectionHeading>
        <div className="grid grid-cols-2 gap-3">
          <FieldInput label="Highest Education" fieldKey="education_level" value={values.education_level ?? ''} onChange={onChange} placeholder="e.g. Bachelor of Commerce" />
        </div>
      </div>

      <div>
        <SectionHeading>Skills &amp; Bio</SectionHeading>
        <div className="grid grid-cols-2 gap-3">
          <FieldTextarea
            label="Skills (comma-separated)"
            fieldKey="skills"
            value={values.skills ?? ''}
            onChange={onChange}
            placeholder="e.g. Project Management, Stakeholder Engagement, Excel"
            rows={3}
          />
          <FieldTextarea
            label="Cover Letter / Bio"
            fieldKey="cover_letter_blurb"
            value={values.cover_letter_blurb ?? ''}
            onChange={onChange}
            placeholder="A short bio or cover letter opening paragraph…"
            rows={5}
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tabbed form
// ---------------------------------------------------------------------------

interface ProfileFormProps {
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

function ProfileForm({ values, onChange }: ProfileFormProps) {
  const [activeTab, setActiveTab] = useState<TabId>('personal');

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-1 p-1 bg-[#F5F5F7] rounded-xl mb-5">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer
              ${activeTab === tab.id
                ? 'bg-white shadow-sm border border-[#E5E5EA]/60 text-[#1D1D1F]'
                : 'text-[#86868B] hover:text-[#1D1D1F]'
              }
            `}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Panel */}
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.15, ease: 'easeInOut' }}
        >
          {activeTab === 'personal' && <PersonalTab values={values} onChange={onChange} />}
          {activeTab === 'address' && <AddressTab values={values} onChange={onChange} />}
          {activeTab === 'professional' && <ProfessionalTab values={values} onChange={onChange} />}
          {activeTab === 'online' && <OnlineTab values={values} onChange={onChange} />}
          {activeTab === 'resume' && <ResumeTab values={values} onChange={onChange} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ProfilesPage() {
  useEffect(() => { document.title = 'Data Profiles — Slate'; }, []);

  const [profiles, setProfiles] = useState<DataProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<DataProfile | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Form state
  const [profileName, setProfileName] = useState('');
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [isDefault, setIsDefault] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfiles = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/profiles');
      const json = await res.json();
      if (json.success) {
        setProfiles(json.data);
      }
    } catch {
      console.error('Failed to fetch profiles');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const openCreateModal = () => {
    setEditingProfile(null);
    setProfileName('');
    setFieldValues({});
    setIsDefault(false);
    setError(null);
    setModalOpen(true);
  };

  const openEditModal = (profile: DataProfile) => {
    setEditingProfile(profile);
    setProfileName(profile.name);
    setFieldValues({ ...profile.data });
    setIsDefault(profile.isDefault);
    setError(null);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingProfile(null);
  };

  const handleFieldChange = (key: string, value: string) => {
    setFieldValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (!profileName.trim()) {
      setError('Profile name is required.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Strip empty values
      const cleanData: Record<string, string> = {};
      for (const [k, v] of Object.entries(fieldValues)) {
        if (v && v.trim()) cleanData[k] = v.trim();
      }

      if (editingProfile) {
        const res = await fetch(`/api/profiles/${editingProfile.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: profileName.trim(), data: cleanData, isDefault }),
        });
        const json = await res.json();
        if (!json.success) {
          setError(json.error?.message ?? 'Failed to update profile.');
          return;
        }
      } else {
        const res = await fetch('/api/profiles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: profileName.trim(), data: cleanData, isDefault }),
        });
        const json = await res.json();
        if (!json.success) {
          setError(json.error?.message ?? 'Failed to create profile.');
          return;
        }
      }

      closeModal();
      await fetchProfiles();
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      const res = await fetch(`/api/profiles/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.success) {
        setProfiles((prev) => prev.filter((p) => p.id !== id));
      }
    } catch {
      console.error('Failed to delete profile');
    } finally {
      setDeleting(null);
      setDeleteConfirmId(null);
    }
  };

  const handleToggleDefault = async (profile: DataProfile) => {
    try {
      const res = await fetch(`/api/profiles/${profile.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isDefault: !profile.isDefault }),
      });
      const json = await res.json();
      if (json.success) {
        await fetchProfiles();
      }
    } catch {
      console.error('Failed to toggle default');
    }
  };

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const listVariants = {
    hidden: {},
    visible: {
      transition: { staggerChildren: prefersReducedMotion ? 0 : 0.06 },
    },
  };

  const itemVariants: import('framer-motion').Variants = prefersReducedMotion
    ? { hidden: {}, visible: {} }
    : {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
      };

  return (
    <div className="max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Data Profiles</h1>
          <p className="text-sm text-[#86868B] mt-1">
            Save your information to auto-fill forms faster.
          </p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus size={16} />
          New Profile
        </Button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={28} className="animate-spin text-[#86868B]" />
        </div>
      )}

      {/* Empty State */}
      {!loading && profiles.length === 0 && (
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <Card className="py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mx-auto">
              <User size={28} className="text-[#AEAEB2]" />
            </div>
            <h3 className="text-base font-semibold text-[#1D1D1F] mt-5">No profiles yet</h3>
            <p className="text-sm text-[#86868B] mt-2 max-w-sm mx-auto">
              Create a data profile to auto-fill your details into any form.
            </p>
            <Button variant="secondary" size="sm" className="mt-5" onClick={openCreateModal}>
              Create Profile
            </Button>
          </Card>
        </motion.div>
      )}

      {/* Profile List */}
      {!loading && profiles.length > 0 && (
        <motion.div
          className="space-y-3"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {profiles.map((profile) => (
            <motion.div key={profile.id} variants={itemVariants}>
              <Card hover className="flex items-center gap-4 cursor-pointer group" onClick={() => openEditModal(profile)}>
                {/* Icon */}
                <div className="w-10 h-10 rounded-xl bg-[#F5F5F7] flex items-center justify-center shrink-0 group-hover:bg-[#5856D6]/10 transition-colors duration-200">
                  <User size={18} className="text-[#86868B] group-hover:text-[#5856D6] transition-colors duration-200" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-[#1D1D1F] truncate">
                      {profile.name}
                    </span>
                    {profile.isDefault && <Badge variant="accent">Default</Badge>}
                  </div>
                  <p className="text-xs text-[#86868B] mt-0.5">
                    {filledFieldCount(profile.data)} fields filled
                    <span className="mx-1.5">&middot;</span>
                    Created {formatDate(profile.createdAt)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleToggleDefault(profile)}
                    className="p-2 rounded-lg hover:bg-[#F5F5F7] transition-colors cursor-pointer"
                    title={profile.isDefault ? 'Remove default' : 'Set as default'}
                  >
                    <Star
                      size={16}
                      className={profile.isDefault ? 'text-[#FF9F0A] fill-[#FF9F0A]' : 'text-[#86868B]'}
                    />
                  </button>
                  <button
                    onClick={() => openEditModal(profile)}
                    className="p-2 rounded-lg hover:bg-[#F5F5F7] transition-colors cursor-pointer"
                    title="Edit profile"
                  >
                    <Pencil size={16} className="text-[#86868B]" />
                  </button>
                  <button
                    onClick={() => setDeleteConfirmId(profile.id)}
                    className="p-2 rounded-lg hover:bg-[#FF3B30]/10 transition-colors cursor-pointer"
                    title="Delete profile"
                  >
                    <Trash2 size={16} className="text-[#86868B] hover:text-[#FF3B30]" />
                  </button>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Create / Edit Profile Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={closeModal}
        title={editingProfile ? 'Edit Profile' : 'New Data Profile'}
        size="lg"
      >
        <div className="space-y-4 max-h-[65vh] overflow-y-auto pr-1">
          {/* Profile name + default toggle */}
          <div className="flex gap-3 items-end">
            <div className="flex-1 flex flex-col gap-1.5">
              <label className="text-sm font-medium text-[#1D1D1F]">Profile Name</label>
              <input
                type="text"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                placeholder='e.g. "Personal", "Business", "Client — Acme"'
                className="h-10 px-3 rounded-xl border border-[#E5E5EA] bg-white text-sm text-[#1D1D1F] placeholder:text-[#AEAEB2] transition-all duration-200 hover:border-[#C7C7CC] focus:outline-none focus:ring-2 focus:ring-[#5856D6]/20 focus:border-[#5856D6]"
              />
            </div>
            <div className="flex items-center gap-2 pb-0.5">
              <button
                type="button"
                onClick={() => setIsDefault(!isDefault)}
                className={`relative w-10 h-6 rounded-full transition-colors duration-200 cursor-pointer ${isDefault ? 'bg-[#5856D6]' : 'bg-[#E5E5EA]'}`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${isDefault ? 'translate-x-4' : 'translate-x-0'}`}
                />
              </button>
              <span className="text-sm text-[#1D1D1F] whitespace-nowrap">Set as default</span>
            </div>
          </div>

          {/* Tabbed fields */}
          <div className="border-t border-[#E5E5EA] pt-4 mt-2">
            <ProfileForm values={fieldValues} onChange={handleFieldChange} />
          </div>

          {error && (
            <p className="text-sm text-[#FF3B30] bg-[#FF3B30]/5 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-[#E5E5EA] mt-4">
          <Button variant="ghost" onClick={closeModal}>
            Cancel
          </Button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="bg-[#5856D6] text-white rounded-xl px-6 py-2.5 text-sm font-semibold transition-all duration-150 hover:bg-[#4A48C4] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            {editingProfile ? 'Save Changes' : 'Create Profile'}
          </button>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteConfirmId}
        onClose={() => setDeleteConfirmId(null)}
        title="Delete Profile"
        size="sm"
      >
        <p className="text-sm text-[#86868B]">
          Are you sure you want to delete this profile? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3 pt-4 mt-4 border-t border-[#E5E5EA]">
          <Button variant="ghost" onClick={() => setDeleteConfirmId(null)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={deleting === deleteConfirmId}
            onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
