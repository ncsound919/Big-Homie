import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Prisma } from '@prisma/client';

const { dbMock } = vi.hoisted(() => ({
  dbMock: {
    agent: {
      create: vi.fn(),
      delete: vi.fn(),
      findMany: vi.fn(),
      update: vi.fn(),
    },
  },
}));

vi.mock('@/lib/db', () => ({
  db: dbMock,
}));

import { DELETE, GET, POST, PUT } from '@/app/api/agents/route';

const LOCAL_HEADERS = {
  origin: 'http://localhost:3000',
};

describe('agents route', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    delete process.env.BIG_HOMIE_AGENT_API_KEY;
    delete process.env.AGENT_API_KEY;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('rejects GET requests without auth context', async () => {
    const response = await GET(new Request('http://localhost/api/agents'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ error: 'Unauthorized' });
  });

  it('returns a redacted list for trusted local requests', async () => {
    dbMock.agent.findMany.mockResolvedValue([
      {
        id: 'agent-1',
        name: 'Test Agent',
        description: 'desc',
        type: 'config',
        config: { hello: 'world' },
        code: 'console.log("secret")',
        securityTier: 'full',
        enabled: true,
        addedAt: new Date('2026-04-16T00:00:00.000Z'),
      },
    ]);

    const response = await GET(
      new Request('http://localhost/api/agents', {
        headers: LOCAL_HEADERS,
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body).toEqual([
      {
        id: 'agent-1',
        name: 'Test Agent',
        description: 'desc',
        type: 'config',
        securityTier: 'full',
        enabled: true,
        addedAt: '2026-04-16T00:00:00.000Z',
      },
    ]);
  });

  it('returns sensitive fields only for API-key authorized requests', async () => {
    process.env.BIG_HOMIE_AGENT_API_KEY = 'agent-secret';
    dbMock.agent.findMany.mockResolvedValue([
      {
        id: 'agent-1',
        name: 'Sensitive Agent',
        description: null,
        type: 'code',
        config: null,
        code: 'console.log("secret")',
        securityTier: 'reduced',
        enabled: false,
        addedAt: new Date('2026-04-16T00:00:00.000Z'),
      },
    ]);

    const response = await GET(
      new Request('http://localhost/api/agents?includeSensitive=1', {
        headers: {
          Authorization: 'Bearer agent-secret',
        },
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body[0]).toMatchObject({
      code: 'console.log("secret")',
      config: null,
    });
  });

  it('creates agents and clears stale config/code when type changes', async () => {
    dbMock.agent.create.mockResolvedValue({ id: 'created-agent' });
    dbMock.agent.update.mockResolvedValue({ id: 'updated-agent' });

    const createResponse = await POST(
      new Request('http://localhost/api/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...LOCAL_HEADERS,
        },
        body: JSON.stringify({
          name: 'Created Agent',
          description: 'desc',
          type: 'config',
          config: { mode: 'safe' },
          securityTier: 'full',
          enabled: true,
        }),
      }),
    );

    expect(createResponse.status).toBe(200);
    expect(dbMock.agent.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: 'config',
          config: { mode: 'safe' },
          code: null,
        }),
      }),
    );

    const updateResponse = await POST(
      new Request('http://localhost/api/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...LOCAL_HEADERS,
        },
        body: JSON.stringify({
          id: 'agent-1',
          name: 'Updated Agent',
          description: 'desc',
          type: 'code',
          code: 'export const agent = true;',
          config: { stale: true },
          securityTier: 'reduced',
          enabled: false,
        }),
      }),
    );

    expect(updateResponse.status).toBe(200);
    expect(dbMock.agent.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'agent-1' },
        data: expect.objectContaining({
          type: 'code',
          code: 'export const agent = true;',
          config: Prisma.JsonNull,
        }),
      }),
    );
  });

  it('creates folder agents and stores files in config field', async () => {
    dbMock.agent.create.mockResolvedValue({ id: 'folder-agent' });

    const folderFiles = { 'src/index.ts': 'console.log("hi")', 'package.json': '{}' };

    const response = await POST(
      new Request('http://localhost/api/agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...LOCAL_HEADERS,
        },
        body: JSON.stringify({
          name: 'My CLI',
          description: 'A CLI project',
          type: 'folder',
          files: folderFiles,
          securityTier: 'reduced',
          enabled: true,
        }),
      }),
    );

    expect(response.status).toBe(200);
    expect(dbMock.agent.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          type: 'folder',
          config: folderFiles,
          code: null,
        }),
      }),
    );
  });

  it('returns files field for folder agents in sensitive GET', async () => {
    process.env.BIG_HOMIE_AGENT_API_KEY = 'agent-secret';
    const folderFiles = { 'main.py': 'print("hello")' };
    dbMock.agent.findMany.mockResolvedValue([
      {
        id: 'folder-1',
        name: 'My Folder Agent',
        description: 'desc',
        type: 'folder',
        config: folderFiles,
        code: null,
        securityTier: 'full',
        enabled: true,
        addedAt: new Date('2026-04-16T00:00:00.000Z'),
      },
    ]);

    const response = await GET(
      new Request('http://localhost/api/agents?includeSensitive=1', {
        headers: {
          Authorization: 'Bearer agent-secret',
        },
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body[0]).toMatchObject({
      type: 'folder',
      files: folderFiles,
    });
    expect(body[0].config).toBeUndefined();
  });

  it('omits files field for folder agents in redacted GET', async () => {
    const folderFiles = { 'main.py': 'print("hello")' };
    dbMock.agent.findMany.mockResolvedValue([
      {
        id: 'folder-1',
        name: 'My Folder Agent',
        description: 'desc',
        type: 'folder',
        config: folderFiles,
        code: null,
        securityTier: 'full',
        enabled: true,
        addedAt: new Date('2026-04-16T00:00:00.000Z'),
      },
    ]);

    const response = await GET(
      new Request('http://localhost/api/agents', {
        headers: LOCAL_HEADERS,
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body[0].type).toBe('folder');
    expect(body[0].files).toBeUndefined();
    expect(body[0].config).toBeUndefined();
  });

  it('rejects DELETE without an id', async () => {
    const response = await DELETE(
      new Request('http://localhost/api/agents', {
        method: 'DELETE',
        headers: LOCAL_HEADERS,
      }),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'Missing id' });
  });

  it('rejects PUT without an id', async () => {
    const response = await PUT(
      new Request('http://localhost/api/agents', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...LOCAL_HEADERS,
        },
        body: JSON.stringify({ enabled: true }),
      }),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'Missing id' });
  });
});
