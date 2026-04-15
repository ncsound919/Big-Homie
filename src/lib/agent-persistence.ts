import { db } from '@/lib/db';
import type { CustomAgent } from '@/types/agent';

export async function saveAgent(agent: CustomAgent): Promise<CustomAgent> {
  const result = await db.agent.upsert({
    where: { id: agent.id || '' },
    update: {
      name: agent.name,
      description: agent.description,
      type: agent.type,
      config: agent.type === 'config' ? agent.config as object : undefined,
      code: agent.type === 'code' ? agent.code : undefined,
      securityTier: agent.securityTier,
      enabled: agent.enabled,
    },
    create: {
      id: agent.id,
      name: agent.name,
      description: agent.description,
      type: agent.type,
      config: agent.type === 'config' ? agent.config as object : undefined,
      code: agent.type === 'code' ? agent.code : undefined,
      securityTier: agent.securityTier,
      enabled: agent.enabled,
      addedAt: new Date(),
    },
  });

  return {
    id: result.id,
    name: result.name,
    description: result.description || undefined,
    type: result.type as 'config' | 'code',
    config: result.config as object | undefined,
    code: result.code || undefined,
    securityTier: result.securityTier as 'full' | 'reduced' | 'custom',
    enabled: result.enabled,
    addedAt: result.addedAt.toISOString(),
  };
}

export async function getAgents(): Promise<CustomAgent[]> {
  const agents = await db.agent.findMany({
    orderBy: { addedAt: 'desc' },
  });

  return agents.map(a => ({
    id: a.id,
    name: a.name,
    description: a.description || undefined,
    type: a.type as 'config' | 'code',
    config: a.config as object | undefined,
    code: a.code || undefined,
    securityTier: a.securityTier as 'full' | 'reduced' | 'custom',
    enabled: a.enabled,
    addedAt: a.addedAt.toISOString(),
  }));
}

export async function deleteAgent(id: string): Promise<void> {
  await db.agent.delete({ where: { id } });
}

export async function toggleAgent(id: string, enabled: boolean): Promise<void> {
  await db.agent.update({
    where: { id },
    data: { enabled },
  });
}