import { useState, useRef } from 'react';
import { Upload, X, FileJson, FileCode, FolderOpen, AlertCircle, CheckCircle } from 'lucide-react';

import { type CustomAgent } from '../types/agent';

interface AgentUploadModalProps {
  onUpload: (agent: CustomAgent) => void;
  onClose: () => void;
}

const TEXT_EXTENSIONS = new Set([
  '.json', '.js', '.ts', '.jsx', '.tsx', '.py', '.md', '.txt', '.yaml', '.yml',
  '.toml', '.cfg', '.ini', '.env', '.sh', '.bat', '.css', '.html', '.xml',
  '.csv', '.sql', '.graphql', '.proto', '.rs', '.go', '.java', '.kt', '.rb',
  '.php', '.c', '.cpp', '.h', '.hpp', '.cs', '.swift', '.r', '.lua',
  '.dockerfile', '.gitignore', '.editorconfig', '.prettierrc', '.eslintrc',
]);

const EXTENSIONLESS_TEXT_FILES = new Set([
  'makefile', 'dockerfile', 'procfile', 'gemfile', 'rakefile', 'license', 'readme',
]);

function isTextFile(name: string): boolean {
  const lower = name.toLowerCase();
  const dot = lower.lastIndexOf('.');
  if (dot === -1) {
    const base = lower.split('/').pop() ?? '';
    return EXTENSIONLESS_TEXT_FILES.has(base);
  }
  return TEXT_EXTENSIONS.has(lower.substring(dot));
}

export default function AgentUploadModal({ onUpload, onClose }: AgentUploadModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<'config' | 'code' | 'folder'>('config');
  const [securityTier, setSecurityTier] = useState<'full' | 'reduced' | 'custom'>('reduced');
  const [file, setFile] = useState<File | null>(null);
  const [folderFiles, setFolderFiles] = useState<File[]>([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const allowedConfigExt = ['.json'];
    const allowedCodeExt = ['.js', '.ts', '.jsx', '.tsx'];

    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();

    if (type === 'config' && !allowedConfigExt.includes(ext)) {
      setError('Please upload a .json file for config type');
      setFile(null);
      return;
    }

    if (type === 'code' && !allowedCodeExt.includes(ext)) {
      setError('Please upload a .js, .ts, .jsx, or .tsx file for code type');
      setFile(null);
      return;
    }

    setError('');
    setSuccess('');
    setFile(selectedFile);
  };

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const selected = Array.from(files).filter((f) => isTextFile(f.webkitRelativePath || f.name));

    if (selected.length === 0) {
      setError('No scannable text files found in the selected folder');
      setFolderFiles([]);
      return;
    }

    setError('');
    setSuccess(`${selected.length} file${selected.length === 1 ? '' : 's'} detected`);
    setFolderFiles(selected);
  };

  const handleTypeChange = (newType: 'config' | 'code' | 'folder') => {
    setType(newType);
    setFile(null);
    setFolderFiles([]);
    setError('');
    setSuccess('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (folderInputRef.current) {
      folderInputRef.current.value = '';
    }
  };

  const validateAndUpload = async () => {
    if (!name.trim()) {
      setError('Please enter a name for the agent');
      return;
    }

    if (type === 'folder') {
      if (folderFiles.length === 0) {
        setError('Please select a folder to upload');
        return;
      }

      const filesMap: Record<string, string> = {};
      for (const f of folderFiles) {
        const relativePath = f.webkitRelativePath || f.name;
        try {
          filesMap[relativePath] = await f.text();
        } catch {
          setError(`Failed to read file: ${relativePath}`);
          return;
        }
      }

      const agent: CustomAgent = {
        id: crypto.randomUUID(),
        name: name.trim(),
        description: description.trim() || `Folder with ${folderFiles.length} files`,
        type: 'folder',
        files: filesMap,
        securityTier,
        enabled: true,
        addedAt: new Date().toISOString(),
      };

      onUpload(agent);
      return;
    }

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    if (type === 'config') {
      try {
        const text = await file.text();
        JSON.parse(text);
        setSuccess('Valid JSON configuration');
      } catch {
        setError('Invalid JSON file. Please upload a valid JSON configuration.');
        return;
      }
    }

    const agent: CustomAgent = {
      id: crypto.randomUUID(),
      name: name.trim(),
      description: description.trim() || undefined,
      type,
      securityTier,
      enabled: true,
      addedAt: new Date().toISOString(),
    };

    onUpload(agent);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md p-6 rounded-2xl bg-background border border-border/30 shadow-xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-background/20 text-muted-foreground transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-4">
          <Upload className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">Upload Agent</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Agent Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter agent name"
              className="w-full px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Description (optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the agent"
              className="w-full px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Agent Type</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleTypeChange('config')}
                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                  type === 'config'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border/30 text-muted-foreground hover:bg-background/20'
                }`}
              >
                <FileJson className="w-3.5 h-3.5" />
                Config (.json)
              </button>
              <button
                type="button"
                onClick={() => handleTypeChange('code')}
                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                  type === 'code'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border/30 text-muted-foreground hover:bg-background/20'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                Code (.js/.ts)
              </button>
              <button
                type="button"
                onClick={() => handleTypeChange('folder')}
                className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                  type === 'folder'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border/30 text-muted-foreground hover:bg-background/20'
                }`}
              >
                <FolderOpen className="w-3.5 h-3.5" />
                Folder
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">Security Tier</label>
            <select
              value={securityTier}
              onChange={(e) => setSecurityTier(e.target.value as 'full' | 'reduced' | 'custom')}
              className="w-full px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="full">Full - Full system access</option>
              <option value="reduced">Reduced - Limited access</option>
              <option value="custom">Custom - User-defined permissions</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-foreground mb-1.5">
              {type === 'folder' ? 'Folder' : 'File'}
            </label>
            {type === 'folder' ? (
              <>
                <input
                  ref={folderInputRef}
                  type="file"
                  /* @ts-expect-error webkitdirectory is a non-standard but widely supported attribute */
                  webkitdirectory=""
                  multiple
                  onChange={handleFolderChange}
                  className="w-full px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-sm text-foreground file:mr-2 file:px-2 file:rounded file:border-0 file:text-xs file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                />
                {folderFiles.length > 0 && (
                  <p className="mt-1.5 text-[10px] text-muted-foreground">
                    {folderFiles.length} text file{folderFiles.length === 1 ? '' : 's'} ready for scan
                  </p>
                )}
              </>
            ) : (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={type === 'config' ? '.json' : '.js,.ts,.jsx,.tsx'}
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-sm text-foreground file:mr-2 file:px-2 file:rounded file:border-0 file:text-xs file:font-medium file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                />
                {file && (
                  <p className="mt-1.5 text-[10px] text-muted-foreground">
                    Selected: {file.name}
                  </p>
                )}
              </>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-destructive/10 text-destructive text-xs">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              {error}
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs">
              <CheckCircle className="w-3.5 h-3.5 shrink-0" />
              {success}
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={validateAndUpload}
          className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-all"
        >
          <Upload className="w-4 h-4" />
          Upload Agent
        </button>
      </div>
    </div>
  );
}