export interface CustomAgent {
  id: string;
  name: string;
  description?: string;
  type: 'config' | 'code' | 'folder';
  config?: object;
  code?: string;
  /** Map of relative file paths to their text contents (folder uploads). */
  files?: Record<string, string>;
  securityTier: 'full' | 'reduced' | 'custom';
  enabled: boolean;
  addedAt: string;
}