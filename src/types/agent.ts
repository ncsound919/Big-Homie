export interface CustomAgent {
  id: string;
  name: string;
  description?: string;
  type: 'config' | 'code';
  config?: object;
  code?: string;
  securityTier: 'full' | 'reduced' | 'custom';
  enabled: boolean;
  addedAt: string;
}