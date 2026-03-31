'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, User, Pencil, Trash2, Star, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { DataProfile, DEFAULT_PROFILE_FIELDS } from '@/types/profile';

function fieldLabel(field: string): string {
  return field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function filledFieldCount(data: Record<string, string>): number {
  return Object.values(data).filter((v) => v && v.trim().length > 0).length;
}

export default function ProfilesPage() {
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

  const handleSave = async () => {
    if (!profileName.trim()) {
      setError('Profile name is required.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Strip empty values from fieldValues
      const cleanData: Record<string, string> = {};
      for (const [k, v] of Object.entries(fieldValues)) {
        if (v && v.trim()) cleanData[k] = v.trim();
      }

      if (editingProfile) {
        // Update
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
        // Create
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
              Create a data profile with your name, address, and other details to auto-fill form
              fields.
            </p>
            <Button variant="secondary" size="sm" className="mt-5" onClick={openCreateModal}>
              Create Your First Profile
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
          <Input
            label="Profile Name"
            placeholder='e.g., "Personal", "Business", "Client - Acme"'
            value={profileName}
            onChange={(e) => setProfileName(e.target.value)}
          />

          <div className="flex items-center gap-3 py-1">
            <button
              type="button"
              onClick={() => setIsDefault(!isDefault)}
              className={`
                relative w-10 h-6 rounded-full transition-colors duration-200 cursor-pointer
                ${isDefault ? 'bg-[#5856D6]' : 'bg-[#E5E5EA]'}
              `}
            >
              <span
                className={`
                  absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm
                  transition-transform duration-200
                  ${isDefault ? 'translate-x-4' : 'translate-x-0'}
                `}
              />
            </button>
            <span className="text-sm text-[#1D1D1F]">Set as default profile</span>
          </div>

          <div className="border-t border-[#E5E5EA] pt-4 mt-4">
            <p className="text-sm font-medium text-[#1D1D1F] mb-3">Profile Fields</p>
            <div className="grid grid-cols-2 gap-3">
              {DEFAULT_PROFILE_FIELDS.map((field) => (
                <Input
                  key={field}
                  label={fieldLabel(field)}
                  placeholder={`Enter ${fieldLabel(field).toLowerCase()}`}
                  value={fieldValues[field] ?? ''}
                  onChange={(e) =>
                    setFieldValues((prev) => ({ ...prev, [field]: e.target.value }))
                  }
                />
              ))}
            </div>
          </div>

          {error && (
            <p className="text-sm text-[#FF3B30] bg-[#FF3B30]/5 rounded-lg px-3 py-2">{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-[#E5E5EA] mt-4">
          <Button variant="ghost" onClick={closeModal}>
            Cancel
          </Button>
          <Button onClick={handleSave} loading={saving}>
            {editingProfile ? 'Save Changes' : 'Create Profile'}
          </Button>
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
