import type { SkillDefinition } from '@/types/skill';
import { RECONCILIATION_REPORT_PDFME_MAPPINGS } from '@/lib/pdf/pdfmeTemplates';

export const reconciliationReport: SkillDefinition = {
  id: 'trust_reconciliation_report',
  name: 'Trust Reconciliation Report',
  description:
    'Fill out a trust account reconciliation report. Bank account, cash book, ledger balances, and sign-off.',
  icon: 'Calculator',
  version: '1.0',
  jurisdiction: 'VIC, Australia',
  documentType: 'Trust Account Reconciliation Report',

  sections: [
    {
      id: 'header',
      title: 'Report Details',
      description: 'Report period and account information.',
      fields: [
        {
          id: 'report_date',
          label: 'Report Date',
          type: 'text',
          placeholder: 'e.g. 1/04/2026 11:32 AM',
          required: true,
        },
        {
          id: 'trust_account',
          label: 'Trust Account',
          type: 'text',
          placeholder: 'e.g. (033341) - 811283',
          required: true,
        },
        {
          id: 'report_month',
          label: 'Report Month',
          type: 'text',
          placeholder: 'e.g. March 2026',
          required: true,
        },
      ],
    },
    {
      id: 'bank_account',
      title: 'Bank Account',
      description: 'Bank statement reconciliation details.',
      fields: [
        {
          id: 'bank_balance',
          label: 'Bank Statement Balance',
          type: 'currency',
          placeholder: 'e.g. 52820.17',
          required: true,
        },
        {
          id: 'unrec_deposits',
          label: 'Add: Unreconciled Deposits',
          type: 'currency',
          placeholder: '0.00',
          defaultValue: '0.00',
        },
        {
          id: 'unrec_withdrawals',
          label: 'Less: Unreconciled Withdrawals',
          type: 'currency',
          placeholder: '0.00',
          defaultValue: '0.00',
        },
        {
          id: 'adjustments',
          label: 'Add: Adjustments',
          type: 'currency',
          placeholder: 'e.g. -732.60',
        },
        {
          id: 'cash_not_banked',
          label: 'Add: Cash Not Banked',
          type: 'currency',
          placeholder: '0.00',
          defaultValue: '0.00',
        },
        {
          id: 'withdrawals_not_processed',
          label: 'Less: Withdrawals Not Processed',
          type: 'currency',
          placeholder: '0.00',
          defaultValue: '0.00',
        },
        {
          id: 'reconciled_balance',
          label: 'Reconciled Bank Statement Balance',
          type: 'currency',
          placeholder: 'e.g. 52087.57',
          required: true,
        },
      ],
    },
    {
      id: 'cash_book',
      title: 'Cash Book',
      description: 'Cash book balance details.',
      fields: [
        {
          id: 'balance_brought_forward',
          label: 'Balance Brought Forward',
          type: 'currency',
          placeholder: 'e.g. 54251.47',
          required: true,
        },
        {
          id: 'bf_date',
          label: 'Balance Forward From Date',
          type: 'text',
          placeholder: 'e.g. Sunday, March 1, 2026',
        },
        {
          id: 'new_receipts',
          label: 'Add: New Receipts',
          type: 'currency',
          placeholder: 'e.g. 435047.74',
        },
        {
          id: 'new_withdrawals',
          label: 'Less: New Withdrawals',
          type: 'currency',
          placeholder: 'e.g. 437211.64',
        },
        {
          id: 'cashbook_balance',
          label: 'Balance as at End of Month',
          type: 'currency',
          placeholder: 'e.g. 52087.57',
          required: true,
        },
        {
          id: 'cashbook_date',
          label: 'Balance Date',
          type: 'text',
          placeholder: 'e.g. Tuesday, March 31, 2026',
        },
      ],
    },
    {
      id: 'ledger_balances',
      title: 'Ledger Balances',
      description: 'Breakdown by ledger type.',
      fields: [
        {
          id: 'ledger_owner',
          label: 'Owner',
          type: 'currency',
          placeholder: 'e.g. 27500.78',
        },
        {
          id: 'ledger_supplier',
          label: 'Supplier',
          type: 'currency',
          placeholder: 'e.g. 22444.80',
        },
        {
          id: 'ledger_tenant',
          label: 'Tenant',
          type: 'currency',
          placeholder: 'e.g. 2141.99',
        },
        {
          id: 'ledger_total',
          label: 'Ledger Balances Total',
          type: 'currency',
          placeholder: 'e.g. 52087.57',
          required: true,
        },
        {
          id: 'ledger_date',
          label: 'Ledger Date',
          type: 'text',
          placeholder: 'e.g. Tuesday, March 31, 2026',
        },
      ],
    },
    {
      id: 'sign_off',
      title: 'Sign Off',
      description: 'Verification and signatory details.',
      fields: [
        {
          id: 'balance_difference',
          label: 'Balance Difference',
          type: 'currency',
          placeholder: '0.00',
          defaultValue: '0.00',
          helpText: 'Should be $0.00 if the bank is in balance.',
        },
        {
          id: 'signatory_name',
          label: 'Name',
          type: 'text',
          placeholder: 'e.g. Stuart Grant',
          required: true,
          profileKey: 'full_name',
        },
      ],
    },
  ],

  fieldMappings: [],
  computedFields: [],
  pdfmeFieldMappings: RECONCILIATION_REPORT_PDFME_MAPPINGS,
};
