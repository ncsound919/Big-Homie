import { describe, expect, it } from 'vitest';

import {
  MASSIVE_UPGRADE_SWEEP,
  FIRST_WAVE_SWEEP,
  determineApprovalPlan,
  buildUpgradeRequestMessage,
  type UpgradeSweepRecommendation,
  type UpgradeApprovalPlan,
  type UpgradeLaunchRequest,
  type UpgradeImplementationReport,
} from './upgrade-sweep';

describe('upgrade-sweep models', () => {
  it('MASSIVE_UPGRADE_SWEEP has at least 2 targets', () => {
    expect(MASSIVE_UPGRADE_SWEEP.length).toBeGreaterThanOrEqual(2);
  });

  it('FIRST_WAVE_SWEEP is the first 2 elements', () => {
    expect(FIRST_WAVE_SWEEP).toEqual(MASSIVE_UPGRADE_SWEEP.slice(0, 2));
  });

  it('every target has required fields', () => {
    for (const target of MASSIVE_UPGRADE_SWEEP) {
      expect(target.targetId).toBeTruthy();
      expect(target.targetName).toBeTruthy();
      expect(target.summary).toBeTruthy();
      expect(target.goals.length).toBeGreaterThan(0);
      expect(target.recommendedRepos.length).toBeGreaterThan(0);
    }
  });

  it('every recommended repo has a score and why', () => {
    for (const target of MASSIVE_UPGRADE_SWEEP) {
      for (const repo of target.recommendedRepos) {
        expect(typeof repo.score).toBe('number');
        expect(repo.why).toBeTruthy();
        expect(repo.repo).toMatch(/\//); // repo format: owner/name
      }
    }
  });

  it('recommended repos are sorted by score descending', () => {
    for (const target of MASSIVE_UPGRADE_SWEEP) {
      for (let i = 1; i < target.recommendedRepos.length; i++) {
        expect(target.recommendedRepos[i - 1].score).toBeGreaterThanOrEqual(
          target.recommendedRepos[i].score,
        );
      }
    }
  });
});

describe('determineApprovalPlan', () => {
  function makeFakeTarget(
    targetId: string,
    categories: string[],
  ): UpgradeSweepRecommendation {
    return {
      targetId,
      targetName: targetId,
      icon: 'test',
      color: 'text-white',
      summary: 'test target',
      goals: ['goal'],
      recommendedRepos: categories.map(cat => ({
        name: `repo-${cat}`,
        repo: `owner/repo-${cat}`,
        stars: 10000,
        description: 'test',
        icon: 'test',
        color: 'text-white',
        category: cat as any,
        highlights: [],
        why: 'test',
        score: 5,
      })),
    };
  }

  it('core target + orchestration repo → manual tier', () => {
    const plan = determineApprovalPlan(makeFakeTarget('agentbrowser', ['orchestration']));
    expect(plan.tier).toBe('manual');
    expect(plan.approvalRequired).toBe(true);
    expect(plan.autoExecute).toBe(false);
  });

  it('core target without orchestration → review tier', () => {
    const plan = determineApprovalPlan(makeFakeTarget('draymond', ['agent']));
    expect(plan.tier).toBe('review');
    expect(plan.approvalRequired).toBe(true);
    expect(plan.autoExecute).toBe(false);
  });

  it('non-core target + orchestration repo → review tier', () => {
    const plan = determineApprovalPlan(makeFakeTarget('quality-stack', ['orchestration']));
    expect(plan.tier).toBe('review');
    expect(plan.approvalRequired).toBe(true);
  });

  it('non-core target without orchestration → auto tier', () => {
    const plan = determineApprovalPlan(makeFakeTarget('quality-stack', ['browser']));
    expect(plan.tier).toBe('auto');
    expect(plan.approvalRequired).toBe(false);
    expect(plan.autoExecute).toBe(true);
  });

  it('real targets produce valid plans', () => {
    for (const target of MASSIVE_UPGRADE_SWEEP) {
      const plan = determineApprovalPlan(target);
      expect(['auto', 'review', 'manual']).toContain(plan.tier);
      expect(typeof plan.approvalRequired).toBe('boolean');
      expect(typeof plan.autoExecute).toBe('boolean');
      expect(plan.rationale).toBeTruthy();
    }
  });
});

describe('buildUpgradeRequestMessage', () => {
  it('returns a non-empty string mentioning target name', () => {
    for (const target of MASSIVE_UPGRADE_SWEEP) {
      const msg = buildUpgradeRequestMessage(target);
      expect(typeof msg).toBe('string');
      expect(msg).toContain(target.targetName);
      expect(msg.length).toBeGreaterThan(50);
    }
  });

  it('includes repo names', () => {
    const target = MASSIVE_UPGRADE_SWEEP[0];
    const msg = buildUpgradeRequestMessage(target);
    for (const repo of target.recommendedRepos) {
      expect(msg).toContain(repo.name);
    }
  });
});

describe('UpgradeImplementationReport type shape', () => {
  it('conforms to expected structure', () => {
    const report: UpgradeImplementationReport = {
      finishedAt: new Date().toISOString(),
      durationSeconds: 12.5,
      outcome: 'success',
      touchedSystems: ['agentbrowser', 'draymond'],
      summary: 'Upgraded browser automation layer.',
      followUp: ['Run integration tests', 'Monitor for regressions'],
      model: 'gpt-4',
      costUsd: 0.0032,
    };
    expect(report.outcome).toBe('success');
    expect(report.touchedSystems).toHaveLength(2);
  });

  it('allows optional fields to be missing', () => {
    const report: UpgradeImplementationReport = {
      finishedAt: new Date().toISOString(),
      durationSeconds: 0,
      outcome: 'failure',
      touchedSystems: [],
      summary: 'Failed',
      followUp: [],
    };
    expect(report.model).toBeUndefined();
    expect(report.costUsd).toBeUndefined();
  });
});

describe('UpgradeLaunchRequest type shape', () => {
  it('accepts report field', () => {
    const request: UpgradeLaunchRequest = {
      requestId: 'test-1',
      createdAt: new Date().toISOString(),
      requestedBy: 'test',
      targetId: 'agentbrowser',
      targetName: 'AgentBrowser',
      summary: 'test',
      requestMessage: 'test',
      approvalTier: 'auto',
      approvalRequired: false,
      autoExecute: true,
      approvalRationale: 'test',
      status: 'completed',
      recommendedRepos: [],
      report: {
        finishedAt: new Date().toISOString(),
        durationSeconds: 5,
        outcome: 'success',
        touchedSystems: ['agentbrowser'],
        summary: 'Done',
        followUp: [],
      },
    };
    expect(request.report?.outcome).toBe('success');
  });
});
