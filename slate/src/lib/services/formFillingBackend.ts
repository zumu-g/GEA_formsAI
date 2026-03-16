import type { BackendAnalyzeResponse } from '@/types/formFillingBackend';

const BACKEND_URL = process.env.FORM_FILLING_BACKEND_URL || 'http://localhost:8000';

export async function analyzeForm(pdfBytes: Uint8Array, filename: string = 'form.pdf'): Promise<BackendAnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', new Blob([Buffer.from(pdfBytes)], { type: 'application/pdf' }), filename);

  const res = await fetch(`${BACKEND_URL}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Backend analyze failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export async function fillAgentStream(
  pdfBytes: Uint8Array,
  instructions: string,
  opts: {
    filename?: string;
    sessionId?: string;
    resumeSessionId?: string;
    anthropicApiKey?: string;
    contextFiles?: { bytes: Uint8Array; name: string }[];
  } = {}
): Promise<Response> {
  const formData = new FormData();
  formData.append('file', new Blob([Buffer.from(pdfBytes)], { type: 'application/pdf' }), opts.filename || 'form.pdf');
  formData.append('instructions', instructions);

  if (opts.sessionId) formData.append('user_session_id', opts.sessionId);
  if (opts.resumeSessionId) formData.append('resume_session_id', opts.resumeSessionId);
  if (opts.anthropicApiKey) formData.append('anthropic_api_key', opts.anthropicApiKey);

  if (opts.contextFiles) {
    for (const cf of opts.contextFiles) {
      formData.append('context_files', new Blob([Buffer.from(cf.bytes)]), cf.name);
    }
  }

  const res = await fetch(`${BACKEND_URL}/fill-agent-stream`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Backend fill-stream failed: ${res.status} ${res.statusText}`);
  }

  return res;
}

export async function fillAgent(
  pdfBytes: Uint8Array,
  instructions: string,
  opts: { filename?: string; anthropicApiKey?: string } = {}
): Promise<{ sessionId: string; pdfBytes: ArrayBuffer }> {
  const formData = new FormData();
  formData.append('file', new Blob([Buffer.from(pdfBytes)], { type: 'application/pdf' }), opts.filename || 'form.pdf');
  formData.append('instructions', instructions);
  if (opts.anthropicApiKey) formData.append('anthropic_api_key', opts.anthropicApiKey);

  const res = await fetch(`${BACKEND_URL}/fill-agent`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Backend fill failed: ${res.status} ${res.statusText}`);
  }

  const data = await res.json();
  return {
    sessionId: data.session_id,
    pdfBytes: data.pdf_hex
      ? Uint8Array.from(data.pdf_hex.match(/.{1,2}/g)!.map((b: string) => parseInt(b, 16))).buffer
      : new ArrayBuffer(0),
  };
}

export async function getSessionPdf(sessionId: string): Promise<ArrayBuffer> {
  const res = await fetch(`${BACKEND_URL}/session/${sessionId}/pdf`);
  if (!res.ok) {
    throw new Error(`Failed to get session PDF: ${res.status}`);
  }
  return res.arrayBuffer();
}

export async function getSessionInfo(sessionId: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${BACKEND_URL}/session/${sessionId}`);
  if (!res.ok) {
    throw new Error(`Failed to get session info: ${res.status}`);
  }
  return res.json();
}
