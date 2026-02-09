'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Upload,
  Sparkles,
  Download,
  Zap,
  Shield,
  CreditCard,
  Repeat,
  Users,
  ArrowRight,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';
import { CREDIT_PACKS } from '@/types/credit';

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: "easeOut" as const },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div {...fadeUp}>
            <Badge variant="accent">Now in Public Beta</Badge>
          </motion.div>

          <motion.h1
            {...fadeUp}
            transition={{ ...fadeUp.transition, delay: 0.1 }}
            className="mt-6 text-5xl md:text-7xl font-bold tracking-tight text-[#1D1D1F] leading-[1.05]"
          >
            Fill forms.
            <br />
            <span className="text-[#86868B]">Not your calendar.</span>
          </motion.h1>

          <motion.p
            {...fadeUp}
            transition={{ ...fadeUp.transition, delay: 0.2 }}
            className="mt-6 text-lg md:text-xl text-[#86868B] max-w-2xl mx-auto leading-relaxed"
          >
            Upload a PDF. AI detects the fields. Drag and drop your data.
            Download the filled form. Pay only when you fill — starting at $0.25.
          </motion.p>

          <motion.div
            {...fadeUp}
            transition={{ ...fadeUp.transition, delay: 0.3 }}
            className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3"
          >
            <Link href="/signup">
              <Button size="lg" className="min-w-[200px]">
                Start Filling for Free
                <ArrowRight size={16} />
              </Button>
            </Link>
            <Link href="#how-it-works">
              <Button variant="secondary" size="lg" className="min-w-[200px]">
                See How It Works
              </Button>
            </Link>
          </motion.div>

          <motion.p
            {...fadeUp}
            transition={{ ...fadeUp.transition, delay: 0.4 }}
            className="mt-4 text-sm text-[#AEAEB2]"
          >
            5 free fills. No credit card required.
          </motion.p>
        </div>

        {/* Hero Visual */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4, ease: "easeOut" }}
          className="max-w-5xl mx-auto mt-16"
        >
          <div className="relative rounded-2xl border border-[#E5E5EA] bg-[#F5F5F7] p-8 shadow-xl">
            <div className="flex gap-6">
              {/* Left panel mockup */}
              <div className="w-56 flex-shrink-0 space-y-3">
                <div className="text-xs font-semibold text-[#86868B] uppercase tracking-wider">Fields Detected</div>
                {['Full Name', 'Email Address', 'Company', 'Phone Number', 'Address'].map((field, i) => (
                  <div
                    key={field}
                    className="flex items-center gap-2 p-2.5 rounded-xl bg-white border border-[#E5E5EA] text-sm text-[#1D1D1F] cursor-grab"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-[#5856D6]" />
                    {field}
                    {i < 2 && (
                      <Check size={12} className="ml-auto text-[#34C759]" />
                    )}
                  </div>
                ))}
              </div>
              {/* PDF preview mockup */}
              <div className="flex-1 rounded-xl bg-white border border-[#E5E5EA] p-6 min-h-[300px] flex items-center justify-center">
                <div className="w-full max-w-sm space-y-6 opacity-60">
                  <div className="h-4 bg-[#E5E5EA] rounded w-3/4" />
                  <div className="space-y-3">
                    <div className="h-3 bg-[#E5E5EA] rounded w-full" />
                    <div className="h-3 bg-[#E5E5EA] rounded w-5/6" />
                    <div className="h-3 bg-[#E5E5EA] rounded w-4/6" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="h-8 border-2 border-dashed border-[#5856D6]/30 rounded-lg bg-[#5856D6]/5 flex items-center px-2">
                      <span className="text-xs text-[#5856D6]">John Doe</span>
                    </div>
                    <div className="h-8 border-2 border-dashed border-[#5856D6]/30 rounded-lg bg-[#5856D6]/5 flex items-center px-2">
                      <span className="text-xs text-[#5856D6]">john@acme.co</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="h-3 bg-[#E5E5EA] rounded w-full" />
                    <div className="h-3 bg-[#E5E5EA] rounded w-3/4" />
                  </div>
                  <div className="h-8 border-2 border-dashed border-[#E5E5EA] rounded-lg" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 px-6 bg-[#F5F5F7]/50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1D1D1F]">
              Three steps. Under sixty seconds.
            </h2>
            <p className="mt-4 text-lg text-[#86868B]">
              No learning curve. No setup. No subscription.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Upload,
                step: '01',
                title: 'Upload your PDF',
                description: 'Drag and drop any PDF form. Tax documents, applications, compliance forms — anything.',
              },
              {
                icon: Sparkles,
                step: '02',
                title: 'AI maps the fields',
                description: 'Our AI instantly detects every fillable field. Drag your data onto them, or let AI auto-fill.',
              },
              {
                icon: Download,
                step: '03',
                title: 'Download. Done.',
                description: 'Get your perfectly filled PDF. Save it as a template to fill the same form in one click next time.',
              },
            ].map((item) => (
              <Card key={item.step} padding="lg" className="text-center border-0 bg-white shadow-sm">
                <div className="w-14 h-14 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mx-auto">
                  <item.icon size={24} className="text-[#1D1D1F]" />
                </div>
                <p className="text-xs font-bold text-[#5856D6] mt-5 tracking-wider">{item.step}</p>
                <h3 className="text-lg font-semibold text-[#1D1D1F] mt-2">{item.title}</h3>
                <p className="text-sm text-[#86868B] mt-2 leading-relaxed">{item.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1D1D1F]">
              Everything you need.
              <br />
              <span className="text-[#86868B]">Nothing you don&apos;t.</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Sparkles,
                title: 'AI Field Detection',
                description: 'Upload any PDF and our AI instantly identifies every fillable field — text boxes, checkboxes, dates, signatures.',
              },
              {
                icon: Zap,
                title: 'One-Click Templates',
                description: 'Save any filled form as a template. Fill the same form next time with a single click.',
              },
              {
                icon: CreditCard,
                title: 'Pay Per Use',
                description: 'No subscriptions. No monthly bills. Buy credits when you need them, starting at $0.10 each.',
              },
              {
                icon: Repeat,
                title: 'Recurring Fills',
                description: 'Schedule forms to fill automatically — weekly, monthly, or on custom schedules.',
              },
              {
                icon: Users,
                title: 'Data Profiles',
                description: 'Save your info once — name, address, company details. Drag and drop onto any form field.',
              },
              {
                icon: Shield,
                title: 'Bank-Grade Security',
                description: 'AES-256 encryption, SOC 2 compliant. Your documents are encrypted and never used for AI training.',
              },
            ].map((feature) => (
              <Card key={feature.title} hover padding="lg">
                <div className="w-10 h-10 rounded-xl bg-[#F5F5F7] flex items-center justify-center">
                  <feature.icon size={20} className="text-[#1D1D1F]" />
                </div>
                <h3 className="text-base font-semibold text-[#1D1D1F] mt-4">{feature.title}</h3>
                <p className="text-sm text-[#86868B] mt-2 leading-relaxed">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 px-6 bg-[#F5F5F7]/50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1D1D1F]">
              Pay for what you use.
            </h2>
            <p className="mt-4 text-lg text-[#86868B]">
              No subscriptions. No commitments. Credits never expire.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {CREDIT_PACKS.map((pack) => (
              <Card
                key={pack.id}
                hover
                padding="lg"
                className={`relative flex flex-col ${
                  pack.popular ? 'border-[#5856D6] ring-1 ring-[#5856D6]/20' : 'bg-white'
                }`}
              >
                {pack.popular && (
                  <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
                    <Badge variant="accent">Most Popular</Badge>
                  </div>
                )}
                <h3 className="text-base font-semibold text-[#1D1D1F]">{pack.name}</h3>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-[#1D1D1F]">${pack.price.toFixed(2)}</span>
                </div>
                <p className="text-sm text-[#86868B] mt-1">{pack.credits} credits</p>

                <ul className="mt-6 space-y-2.5 flex-1">
                  <li className="flex items-center gap-2 text-sm text-[#86868B]">
                    <Check size={14} className="text-[#34C759] flex-shrink-0" />
                    ${pack.pricePerCredit.toFixed(2)} per fill
                  </li>
                  <li className="flex items-center gap-2 text-sm text-[#86868B]">
                    <Check size={14} className="text-[#34C759] flex-shrink-0" />
                    Save {pack.savings}%
                  </li>
                  <li className="flex items-center gap-2 text-sm text-[#86868B]">
                    <Check size={14} className="text-[#34C759] flex-shrink-0" />
                    Never expires
                  </li>
                </ul>

                <Link href="/signup" className="mt-6 block">
                  <Button
                    variant={pack.popular ? 'primary' : 'secondary'}
                    className="w-full"
                  >
                    Get Started
                  </Button>
                </Link>
              </Card>
            ))}
          </div>

          <p className="text-center text-sm text-[#AEAEB2] mt-8">
            Start with 5 free credits. No credit card required.
          </p>
        </div>
      </section>

      {/* Social Proof / Stats */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {[
              { stat: '60s', label: 'Average time to fill a form' },
              { stat: '$0.25', label: 'Starting cost per form fill' },
              { stat: '99.2%', label: 'AI field detection accuracy' },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-4xl md:text-5xl font-bold text-[#1D1D1F]">{item.stat}</p>
                <p className="text-sm text-[#86868B] mt-2">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-[#1D1D1F]">
            Stop filling forms manually.
          </h2>
          <p className="mt-4 text-lg text-[#86868B]">
            Join thousands of businesses that save hours every week with Slate.
          </p>
          <div className="mt-8">
            <Link href="/signup">
              <Button size="lg" className="min-w-[240px]">
                Get Started Free
                <ArrowRight size={16} />
              </Button>
            </Link>
          </div>
          <p className="mt-3 text-sm text-[#AEAEB2]">
            5 free fills. No credit card. No subscription.
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
