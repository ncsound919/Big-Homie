import type { CustomAgent } from '@/types/agent';

const API_BASE = '/api/agents';

export async function getAgents(): Promise<CustomAgent[]> {
  const res = await fetch(API_BASE, { cache: 'no-store' });
  return res.json();
}

export async function saveAgent(agent: CustomAgent): Promise<CustomAgent> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agent),
  });
  return res.json();
}

export async function deleteAgent(id: string): Promise<void> {
  await fetch(`${API_BASE}?id=${id}`, { method: 'DELETE' });
}

export async function toggleAgent(id: string, enabled: boolean): Promise<void> {
  await fetch(API_BASE, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, enabled }),
  });
}