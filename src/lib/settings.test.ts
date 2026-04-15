import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DEFAULT_INTEGRATIONS,
  getActiveAgents,
  getEnabledIntegrations,
  getSettings,
  saveSettings,
  type AppSettings,
} from '@/lib/settings';

const makeSettings = (overrides: Partial<AppSettings> = {}): AppSettings => ({
  mode: 'dev',
  modelProvider: 'local',
  localModel: {
    provider: 'ollama',
    endpoint: 'http://localhost:11434',
    modelName: 'llama3.1',
    apiKey: '',
  },
  customAgents: [],
  integrations: DEFAULT_INTEGRATIONS.map(integration => ({ ...integration })),
  pipeline: {
    autoFix: true,
    skipAudit: false,
    parallelPhases: false,
    defaultSpeed: 1,
  },
  ui: {
    particles: true,
    animations: true,
    compactView: false,
    showTechDetails: false,
  },
  ...overrides,
});

describe('settings store', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('returns defaults when storage is empty or invalid', () => {
    expect(getSettings().mode).toBe('easy');

    localStorage.setItem('ab_settings', '{bad json');
    expect(getSettings().mode).toBe('easy');
  });

  it('deep merges persisted settings with defaults', () => {
    localStorage.setItem(
      'ab_settings',
      JSON.stringify({
        mode: 'dev',
        pipeline: { defaultSpeed: 2 },
        ui: { particles: false },
      })
    );

    const settings = getSettings();

    expect(settings.mode).toBe('dev');
    expect(settings.pipeline.defaultSpeed).toBe(2);
    expect(settings.pipeline.autoFix).toBe(true);
    expect(settings.ui.particles).toBe(false);
    expect(settings.ui.animations).toBe(true);
  });

  it('persists settings and dispatches a change event', () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');
    const settings = makeSettings();

    saveSettings(settings);

    expect(JSON.parse(localStorage.getItem('ab_settings') || '{}')).toMatchObject({ mode: 'dev' });
    expect(dispatchSpy).toHaveBeenCalledTimes(1);
  });

  it('filters integrations by enabled state, API key, and phase', () => {
    saveSettings(
      makeSettings({
        integrations: DEFAULT_INTEGRATIONS.map(integration => ({
          ...integration,
          enabled: integration.id === 'vercel' || integration.id === 'openai',
          apiKey: integration.id === 'vercel' || integration.id === 'openai' ? 'secret-key' : '',
        })),
      })
    );

    expect(getEnabledIntegrations().map(item => item.id)).toEqual(['vercel', 'openai']);
    expect(getEnabledIntegrations(12).map(item => item.id)).toEqual(['vercel']);
    expect(getEnabledIntegrations(1).map(item => item.id)).toEqual(['openai']);
  });

  it('returns only enabled custom agents', () => {
    saveSettings(
      makeSettings({
        customAgents: [
          {
            id: 'agent-1',
            name: 'Enabled Agent',
            description: 'enabled',
            config: '{}',
            fileName: 'enabled.json',
            enabled: true,
            addedAt: '2026-04-10T00:00:00.000Z',
          },
          {
            id: 'agent-2',
            name: 'Disabled Agent',
            description: 'disabled',
            config: '{}',
            fileName: 'disabled.json',
            enabled: false,
            addedAt: '2026-04-10T00:00:00.000Z',
          },
        ],
      })
    );

    expect(getActiveAgents().map(agent => agent.id)).toEqual(['agent-1']);
  });
});