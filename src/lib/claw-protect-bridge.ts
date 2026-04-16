// ClawProtectBridge - AgentBrowser Integration
// Exposes Claw Protect UI components to AgentBrowser

// =============================================================================
// COMPONENT MAPPING
// =============================================================================

export type ClawComponent = 
  | 'ProtectedDialog'
  | 'ProtectedSheet'
  | 'ProtectedDrawer'
  | 'ProtectedPopover'
  | 'ProtectedTooltip'
  | 'SecureInput'
  | 'SecureTextarea'
  | 'AuditLogger'
  | 'RateLimiter';

export interface ComponentConfig {
  name: ClawComponent;
  props?: Record<string, unknown>;
  protected: boolean;
  auditEnabled: boolean;
  rateLimited?: number;
}

export interface OrchestratorLike {
  log?: (event: string, payload: AuditEntry) => void;
}

type OrchestratorFactory = () => OrchestratorLike | undefined;

let orchestratorFactory: OrchestratorFactory | undefined;

export function setClawProtectOrchestratorFactory(factory?: OrchestratorFactory): void {
  orchestratorFactory = factory;
}

// =============================================================================
// BRIDGE IMPLEMENTATION
// =============================================================================

class ClawProtectBridge {
  private components: Map<ClawComponent, boolean> = new Map();
  private auditLog: AuditEntry[] = [];

  async initialize(): Promise<boolean> {
    // Initialize available components from Claw Protect
    console.log('[ClawProtectBridge] Initializing...');
    
    const componentList: ClawComponent[] = [
      'ProtectedDialog',
      'ProtectedSheet', 
      'ProtectedDrawer',
      'ProtectedPopover',
      'ProtectedTooltip',
      'SecureInput',
      'SecureTextarea',
      'AuditLogger',
      'RateLimiter',
    ];

    for (const comp of componentList) {
      this.components.set(comp, true);
    }

    console.log('[ClawProtectBridge] Initialized with components:', componentList);
    return true;
  }

  isAvailable(component: ClawComponent): boolean {
    return this.components.get(component) ?? false;
  }

  getAvailableComponents(): ClawComponent[] {
    return Array.from(this.components.keys()).filter(c => this.components.get(c));
  }

  // Protected dialog with audit logging
  async showProtectedDialog(config: ComponentConfig): Promise<boolean> {
    if (!config.protected) {
      return true;
    }

    this.logAudit({
      component: config.name,
      action: 'show',
      timestamp: new Date(),
      userId: 'current-user',
    });

    if (config.rateLimited) {
      return this.checkRateLimit(config.name, config.rateLimited);
    }

    return true;
  }

  private checkRateLimit(component: string, limit: number): boolean {
    const now = Date.now();
    const recentCalls = this.auditLog.filter(
      entry => entry.component === component &&
      now - entry.timestamp.getTime() < 60000
    );

    if (recentCalls.length >= limit) {
      this.logAudit({
        component,
        action: 'rate_limit_exceeded',
        timestamp: new Date(),
        userId: 'current-user',
      });
      return false;
    }

    return true;
  }

  private logAudit(entry: AuditEntry): void {
    this.auditLog.push(entry);
    
    try {
      orchestratorFactory?.()?.log?.('claw_protect_audit', entry);
    } catch {
      // Ignore errors
    }
  }

  getAuditLog(): AuditEntry[] {
    return [...this.auditLog];
  }

  clearAuditLog(): void {
    this.auditLog = [];
  }
}

export interface AuditEntry {
  component: string;
  action: string;
  timestamp: Date;
  userId: string;
  metadata?: Record<string, unknown>;
}

// Singleton instance
export const clawProtectBridge = new ClawProtectBridge();
export default ClawProtectBridge;
