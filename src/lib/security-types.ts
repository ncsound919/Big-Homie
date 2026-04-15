export type SecurityLevel = 'passive' | 'active' | 'configurable';

export type SecurityResult = {
  approved: boolean;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  warnings: string[];
  blockedReasons: string[];
};

export type SecurityEvent = {
  id: string;
  timestamp: Date;
  action: string;
  result: SecurityResult;
};
