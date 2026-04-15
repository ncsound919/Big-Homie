export interface CustomAgent {
  id: string;
  name: string;
  description?: string;
  type: 'config' | 'code';
  securityTier: 'full' | 'reduced' | 'custom';
  enabled: boolean;
  addedAt: string;
}