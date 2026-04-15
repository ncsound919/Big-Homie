import type { SecurityLevel, SecurityResult, SecurityEvent } from './security-types';

const INJECTION_KEYWORDS = [
  'ignore',
  'ignore previous',
  'disregard',
  'forget',
  'system prompt',
  'new instructions',
  'override',
  'bypass',
  'admin mode',
  'sudo',
  'root access',
  'eval',
  'exec',
  'execSync',
  'spawn',
  'spawnSync',
];

const SECRET_PATTERNS = [
  /api[_-]?key/i,
  /secret/i,
  /password/i,
  /token/i,
  /credential/i,
  /private[_-]?key/i,
  /access[_-]?key/i,
  /auth/i,
];

export class SecurityMiddleware {
  securityLevel: SecurityLevel;
  private events: SecurityEvent[] = [];

  constructor(level: SecurityLevel = 'active') {
    this.securityLevel = level;
  }

  setSecurityLevel(level: SecurityLevel): void {
    this.securityLevel = level;
  }

  async validateAction(
    action: string,
    params: Record<string, unknown>
  ): Promise<SecurityResult> {
    const warnings: string[] = [];
    const blockedReasons: string[] = [];
    let riskLevel: SecurityResult['riskLevel'] = 'low';

    const actionLower = action.toLowerCase();
    const paramsStr = JSON.stringify(params).toLowerCase();

    for (const keyword of INJECTION_KEYWORDS) {
      if (actionLower.includes(keyword) || paramsStr.includes(keyword)) {
        warnings.push(`Potential prompt injection keyword detected: ${keyword}`);
        riskLevel = 'high';
      }
    }

    for (const key of Object.keys(params)) {
      for (const pattern of SECRET_PATTERNS) {
        if (pattern.test(key)) {
          warnings.push(`Potential secret detected in parameter: ${key}`);
          riskLevel = riskLevel === 'high' ? 'high' : 'medium';
        }
      }
    }

    if (warnings.some(w => w.includes('injection'))) {
      riskLevel = 'high';
    } else if (warnings.length > 0 && riskLevel === 'low') {
      riskLevel = 'medium';
    }

    let approved = true;

    if (this.securityLevel === 'active' || this.securityLevel === 'configurable') {
      if (riskLevel === 'high') {
        approved = false;
        blockedReasons.push('High risk action blocked by active security');
      }
    }

    if (this.securityLevel === 'passive' && riskLevel === 'high') {
      warnings.push('High risk action detected in passive mode - allowing but logging warning');
    }

    const result: SecurityResult = {
      approved,
      riskLevel,
      warnings,
      blockedReasons,
    };

    const event: SecurityEvent = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      action,
      result,
    };

    this.logEvent(event);

    return result;
  }

  logEvent(event: SecurityEvent): void {
    this.events.push(event);
  }

  getEvents(): SecurityEvent[] {
    return [...this.events];
  }
}

export const securityMiddleware = new SecurityMiddleware();
