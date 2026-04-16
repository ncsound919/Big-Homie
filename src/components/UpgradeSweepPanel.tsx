'use client';

import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { AppIcon } from '@/lib/icons';
import { formatStars } from '@/lib/trending-repos';
import { ArrowUpRight, CheckCircle2, Clock, Loader2, Rocket, ShieldAlert, TrendingUp, Wrench, XCircle } from 'lucide-react';

import type { ApprovalTier, UpgradeImplementationReport, UpgradeLaunchRequest, UpgradeSweepRecommendation } from '@/lib/upgrade-sweep';

type SweepTarget = UpgradeSweepRecommendation & {
  approval: {
    tier: ApprovalTier;
    approvalRequired: boolean;
    autoExecute: boolean;
    rationale: string;
  };
  activeRequest: UpgradeLaunchRequest | null;
};

interface SweepResponse {
  targets: SweepTarget[];
  queue: UpgradeLaunchRequest[];
  history: UpgradeLaunchRequest[];
}

const TIER_STYLES: Record<ApprovalTier, string> = {
  auto: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  review: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  manual: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

export default function UpgradeSweepPanel() {
  const [data, setData] = useState<SweepResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);

  const loadSweep = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const res = await fetch('/api/upgrade-sweep', { signal });
      if (!res.ok) throw new Error('Failed to load upgrade sweep');
      const payload = await res.json() as SweepResponse;
      if (!signal?.aborted) setData(payload);
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      toast.error('Failed to load upgrade sweep', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    void loadSweep(controller.signal);
    return () => controller.abort();
  }, []);

  const firstWaveTargets = useMemo(() => data?.targets.slice(0, 2) ?? [], [data]);
  const approvalQueue = useMemo(
    () => data?.queue.filter(request => request.status === 'awaiting_approval') ?? [],
    [data],
  );

  const history = useMemo(() => data?.history ?? [], [data]);

  const launchTarget = async (targetId: string) => {
    setActingId(targetId);
    try {
      const res = await fetch('/api/upgrade-sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'launch', targetId }),
      });
      const payload = await res.json() as { request?: UpgradeLaunchRequest; error?: string; deduped?: boolean };
      if (!res.ok || payload.error) throw new Error(payload.error ?? 'Launch failed');

      toast.success(
        payload.request?.autoExecute ? 'Upgrade queued for Draymond' : 'Upgrade queued for approval',
        { description: payload.request?.targetName ?? targetId },
      );
      await loadSweep();
    } catch (error) {
      toast.error('Upgrade launch failed', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActingId(null);
    }
  };

  const approveRequest = async (requestId: string) => {
    setActingId(requestId);
    try {
      const res = await fetch('/api/upgrade-sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve', requestId }),
      });
      const payload = await res.json() as { request?: UpgradeLaunchRequest; error?: string };
      if (!res.ok || payload.error) throw new Error(payload.error ?? 'Approval failed');

      toast.success('Upgrade approved for Draymond', {
        description: payload.request?.targetName ?? requestId,
      });
      await loadSweep();
    } catch (error) {
      toast.error('Approval failed', {
        description: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="w-full rounded-2xl border border-border/30 bg-background/20 overflow-hidden">
      <div className="px-4 sm:px-6 py-4 border-b border-border/30">
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <Wrench className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-foreground">Massive Upgrade Sweep</h3>
          </div>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[9px] font-bold text-cyan-400">
            <Rocket className="w-2.5 h-2.5" />
            Start: AgentBrowser + Draymond
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          One click now spawns upgrade requests for Draymond. Low-risk work auto-runs, architecture-heavy changes pause for approval.
        </p>
      </div>

      <div className="px-4 sm:px-6 py-4 space-y-4">
        {loading && (
          <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-background/20 px-4 py-3 text-xs text-muted-foreground">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Loading live upgrade sweep...
          </div>
        )}

        {!loading && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {firstWaveTargets.map(target => {
                const activeRequest = target.activeRequest;
                const isBusy = actingId === target.targetId || actingId === activeRequest?.requestId;
                return (
                  <div key={target.targetId} className="rounded-xl border border-border/30 bg-background/30 p-4">
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-9 h-9 rounded-xl bg-muted/40 flex items-center justify-center flex-shrink-0">
                        <AppIcon name={target.icon} className={`w-4 h-4 ${target.color}`} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-foreground">{target.targetName}</span>
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[8px] font-bold text-amber-400">
                            <TrendingUp className="w-2 h-2" />
                            Wave 1
                          </span>
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full border text-[8px] font-bold uppercase ${TIER_STYLES[target.approval.tier]}`}>
                            {target.approval.tier}
                          </span>
                        </div>
                        <p className="text-[11px] text-muted-foreground mt-1 leading-relaxed">{target.summary}</p>
                        <p className="text-[10px] text-muted-foreground/80 mt-1">{target.approval.rationale}</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1 mb-3">
                      {target.goals.map(goal => (
                        <span key={goal} className="px-1.5 py-0.5 rounded text-[8px] font-medium border border-border/40 bg-muted/30 text-muted-foreground">
                          {goal}
                        </span>
                      ))}
                    </div>

                    <div className="space-y-2 mb-3">
                      {target.recommendedRepos.map(repo => (
                        <a
                          key={`${target.targetId}-${repo.repo}`}
                          href={`https://github.com/${repo.repo}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group flex items-start gap-3 rounded-lg border border-border/30 bg-background/40 p-3 hover:border-primary/30 hover:bg-primary/5 transition-colors"
                        >
                          <div className="w-8 h-8 rounded-lg bg-muted/40 flex items-center justify-center flex-shrink-0">
                            <AppIcon name={repo.icon} className={`w-4 h-4 ${repo.color}`} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-semibold text-foreground">{repo.name}</span>
                              <span className="text-[9px] text-amber-400 font-medium">{formatStars(repo.stars)}</span>
                              <ArrowUpRight className="w-3 h-3 text-muted-foreground/50 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{repo.why}</p>
                          </div>
                        </a>
                      ))}
                    </div>

                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <div className="text-[10px] text-muted-foreground">
                        {activeRequest
                          ? `Current status: ${activeRequest.status.replace('_', ' ')}`
                          : 'No active Draymond run queued yet.'}
                      </div>
                      <button
                        onClick={() => launchTarget(target.targetId)}
                        disabled={isBusy || !!activeRequest}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary/30 bg-primary/10 text-[11px] font-medium text-primary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/15 transition-colors"
                      >
                        {isBusy && <Loader2 className="w-3 h-3 animate-spin" />}
                        {!isBusy && <Rocket className="w-3 h-3" />}
                        {target.approval.autoExecute ? 'Auto-run via Draymond' : 'Queue for Review'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {approvalQueue.length > 0 && (
              <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <h4 className="text-sm font-semibold text-foreground">Approval Queue</h4>
                </div>
                {approvalQueue.map(request => {
                  const isBusy = actingId === request.requestId;
                  return (
                    <div key={request.requestId} className="flex items-start justify-between gap-3 rounded-lg border border-border/20 bg-background/30 p-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-foreground">{request.targetName}</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{request.approvalRationale}</p>
                      </div>
                      <button
                        onClick={() => approveRequest(request.requestId)}
                        disabled={isBusy}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-[11px] font-medium text-emerald-400 disabled:opacity-50"
                      >
                        {isBusy ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
                        Approve
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {history.length > 0 && (
              <div className="rounded-xl border border-border/20 bg-background/20 p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <h4 className="text-sm font-semibold text-foreground">Run History</h4>
                  <span className="text-[9px] text-muted-foreground">{history.length} runs</span>
                </div>
                {history.slice(0, 10).map(request => {
                  const succeeded = request.status === 'completed';
                  const report = request.report;
                  return (
                    <div key={request.requestId} className={`rounded-lg border p-3 ${succeeded ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-rose-500/20 bg-rose-500/5'}`}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            {succeeded
                              ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                              : <XCircle className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />}
                            <span className="text-xs font-semibold text-foreground">{request.targetName}</span>
                            <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded-full border ${succeeded ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10' : 'text-rose-400 border-rose-500/20 bg-rose-500/10'}`}>
                              {request.status}
                            </span>
                          </div>
                          {report && (
                            <div className="mt-2 space-y-1.5">
                              <p className="text-[10px] text-muted-foreground">{report.summary}</p>
                              {report.touchedSystems.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {report.touchedSystems.map(sys => (
                                    <span key={sys} className="px-1.5 py-0.5 rounded text-[8px] font-medium border border-border/40 bg-muted/30 text-muted-foreground">{sys}</span>
                                  ))}
                                </div>
                              )}
                              {report.followUp.length > 0 && (
                                <div className="text-[9px] text-muted-foreground/80">
                                  Follow-up: {report.followUp.join('; ')}
                                </div>
                              )}
                              <div className="flex items-center gap-3 text-[9px] text-muted-foreground/60">
                                {report.finishedAt && <span>{new Date(report.finishedAt).toLocaleString()}</span>}
                                {report.durationSeconds > 0 && <span>{report.durationSeconds.toFixed(1)}s</span>}
                                {report.costUsd != null && report.costUsd > 0 && <span>${report.costUsd.toFixed(4)}</span>}
                                {report.model && <span>{report.model}</span>}
                              </div>
                            </div>
                          )}
                          {!report && (
                            <p className="text-[10px] text-muted-foreground mt-1">{request.summary}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="flex items-center justify-between gap-3 rounded-xl border border-border/20 bg-muted/20 px-4 py-3">
              <div>
                <p className="text-xs font-semibold text-foreground">Sweep coverage</p>
                <p className="text-[11px] text-muted-foreground">{data?.targets.length ?? 0} target tracks generated from the shared trending repo feed.</p>
              </div>
              <span className="text-[10px] text-muted-foreground">{approvalQueue.length} requests waiting for approval. Auto tier launches are picked up by Draymond heartbeat.</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}