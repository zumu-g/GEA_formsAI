'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookTemplate,
  Globe,
  Hash,
  Plus,
  Search,
  Trash2,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Template } from '@/types/template';
import Link from 'next/link';

const prefersReducedMotion =
  typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

const fadeUp = prefersReducedMotion
  ? {}
  : { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -10 } };

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-[#E5E5EA] p-6 animate-pulse">
      <div className="h-5 bg-[#F5F5F7] rounded-lg w-2/3 mb-3" />
      <div className="h-4 bg-[#F5F5F7] rounded-lg w-full mb-2" />
      <div className="h-4 bg-[#F5F5F7] rounded-lg w-1/2 mb-5" />
      <div className="flex gap-2">
        <div className="h-6 bg-[#F5F5F7] rounded-full w-16" />
        <div className="h-6 bg-[#F5F5F7] rounded-full w-20" />
      </div>
    </div>
  );
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchValue, setSearchValue] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Template | null>(null);
  const [deleting, setDeleting] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchTemplates = useCallback(async (query: string) => {
    setLoading(true);
    try {
      const url = query
        ? `/api/templates?q=${encodeURIComponent(query)}`
        : '/api/templates';
      const res = await fetch(url);
      const json = await res.json();
      if (json.success) {
        setTemplates(json.data);
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch on mount and when debounced query changes
  useEffect(() => {
    fetchTemplates(debouncedQuery);
  }, [debouncedQuery, fetchTemplates]);

  // Debounce search input
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(value.trim());
    }, 300);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/templates/${deleteTarget.id}`, {
        method: 'DELETE',
      });
      const json = await res.json();
      if (json.success) {
        setTemplates((prev) => prev.filter((t) => t.id !== deleteTarget.id));
        setDeleteTarget(null);
      }
    } catch (err) {
      console.error('Failed to delete template:', err);
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Templates</h1>
          <p className="text-sm text-[#86868B] mt-1">
            Save time with reusable form templates.
          </p>
        </div>
        <Link href="/fill">
          <Button>
            <Plus size={16} />
            Create Template
          </Button>
        </Link>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-[#AEAEB2]"
        />
        <Input
          placeholder="Search templates..."
          className="pl-9"
          value={searchValue}
          onChange={handleSearchChange}
        />
      </div>

      {/* Loading skeletons */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && templates.length === 0 && (
        <motion.div
          {...(prefersReducedMotion ? {} : { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } })}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <Card className="py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mx-auto">
              <BookTemplate size={28} className="text-[#AEAEB2]" />
            </div>
            <h3 className="text-base font-semibold text-[#1D1D1F] mt-5">
              {debouncedQuery ? 'No templates match your search' : 'No templates yet'}
            </h3>
            <p className="text-sm text-[#86868B] mt-2 max-w-sm mx-auto">
              {debouncedQuery
                ? 'Try a different search term or create a new template.'
                : 'Fill a form and save it as a template to reuse it with one click next time.'}
            </p>
            {!debouncedQuery && (
              <Link href="/fill" className="inline-block mt-5">
                <Button variant="secondary" size="sm">
                  Fill Your First Form
                </Button>
              </Link>
            )}
          </Card>
        </motion.div>
      )}

      {/* Template grid */}
      {!loading && templates.length > 0 && (
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          {...(prefersReducedMotion ? {} : { initial: { opacity: 0 }, animate: { opacity: 1 } })}
          transition={{ duration: 0.3 }}
        >
          <AnimatePresence mode="popLayout">
            {templates.map((template, index) => (
              <motion.div
                key={template.id}
                layout
                {...fadeUp}
                transition={{
                  duration: 0.35,
                  ease: 'easeOut',
                  delay: prefersReducedMotion ? 0 : index * 0.05,
                }}
              >
                <Card
                  hover
                  className="group relative flex flex-col h-full cursor-pointer"
                >
                  {/* Delete button */}
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setDeleteTarget(template);
                    }}
                    className="absolute top-3 right-3 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-[#FF3B30]/10 transition-all duration-200 cursor-pointer"
                    aria-label={`Delete ${template.name}`}
                  >
                    <Trash2 size={14} className="text-[#FF3B30]" />
                  </button>

                  <Link
                    href={`/fill?templateId=${template.id}`}
                    className="flex flex-col flex-1"
                  >
                    {/* Name */}
                    <h3 className="text-sm font-semibold text-[#1D1D1F] pr-8 line-clamp-1">
                      {template.name}
                    </h3>

                    {/* Description */}
                    {template.description && (
                      <p className="text-xs text-[#86868B] mt-1.5 line-clamp-2 leading-relaxed">
                        {template.description}
                      </p>
                    )}

                    {/* Spacer */}
                    <div className="flex-1 min-h-[12px]" />

                    {/* Meta badges */}
                    <div className="flex flex-wrap items-center gap-2 mt-3">
                      <Badge>
                        <span className="inline-flex items-center gap-1">
                          <Hash size={10} />
                          {template.fieldMappings.length} field{template.fieldMappings.length !== 1 ? 's' : ''}
                        </span>
                      </Badge>

                      <Badge>
                        <span className="inline-flex items-center gap-1">
                          <BarChart3 size={10} />
                          {template.useCount} use{template.useCount !== 1 ? 's' : ''}
                        </span>
                      </Badge>

                      {template.isPublic && (
                        <Badge variant="accent">
                          <span className="inline-flex items-center gap-1">
                            <Globe size={10} />
                            Public
                          </span>
                        </Badge>
                      )}
                    </div>

                    {/* Date */}
                    <p className="text-[11px] text-[#AEAEB2] mt-3">
                      Updated {formatDate(template.updatedAt)}
                    </p>
                  </Link>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Delete confirmation modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => !deleting && setDeleteTarget(null)}
        title="Delete Template"
        size="sm"
      >
        <p className="text-sm text-[#86868B]">
          Are you sure you want to delete{' '}
          <span className="font-medium text-[#1D1D1F]">
            {deleteTarget?.name}
          </span>
          ? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3 mt-6">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setDeleteTarget(null)}
            disabled={deleting}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleDelete}
            loading={deleting}
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
