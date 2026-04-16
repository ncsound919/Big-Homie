'use client';

import { useState, useRef, useCallback, useMemo } from 'react';
import {
  Sparkles, ArrowRight, ArrowLeft, Upload, X, Check,
  MessageSquare, Paperclip, Send, Key, Loader2,
  ShoppingCart, BarChart3, Globe, Bot, Camera, Wrench,
  FileText, Image as ImageIcon, File,
} from 'lucide-react';
import type { ProjectData } from '@/components/ProjectForm';

/* ═══════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════ */
type WizardStep = 'describe' | 'questions' | 'uploads' | 'confirm';

interface ClarifyingQuestion {
  id: string;
  question: string;
  answer: string;
  type: 'text' | 'choice';
  options?: string[];
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
}

interface AuthEntry {
  id: string;
  label: string;
  value: string;
}

export interface EasyModeWizardProps {
  onSubmit: (data: ProjectData) => void;
}

/* ═══════════════════════════════════════════
   SIMPLE PROJECT TEMPLATES (friendly labels)
   ═══════════════════════════════════════════ */
const QUICK_IDEAS = [
  { icon: ShoppingCart, label: 'Online store', type: 'ecommerce' },
  { icon: BarChart3, label: 'Dashboard', type: 'dashboard' },
  { icon: Globe, label: 'Website', type: 'website' },
  { icon: Bot, label: 'Chatbot', type: 'chatbot' },
  { icon: Camera, label: 'Portfolio', type: 'portfolio' },
  { icon: Wrench, label: 'Business tool', type: 'tool' },
];

/* ═══════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════ */
export default function EasyModeWizard({ onSubmit }: EasyModeWizardProps) {
  const [step, setStep] = useState<WizardStep>('describe');
  const [description, setDescription] = useState('');
  const [projectName, setProjectName] = useState('');
  const [questions, setQuestions] = useState<ClarifyingQuestion[]>([]);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [auths, setAuths] = useState<AuthEntry[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const stepIndex = useMemo(() =>
    ['describe', 'questions', 'uploads', 'confirm'].indexOf(step),
  [step]);

  /* ─── Generate clarifying questions from description ─── */
  const generateQuestions = useCallback(() => {
    setIsThinking(true);
    // Simulate AI generating questions based on description
    setTimeout(() => {
      const generated: ClarifyingQuestion[] = [];
      const desc = description.toLowerCase();

      generated.push({
        id: '1', type: 'choice',
        question: 'Who is this for?',
        answer: '',
        options: ['Just me', 'My team', 'My customers', 'The public'],
      });

      if (desc.includes('store') || desc.includes('shop') || desc.includes('sell') || desc.includes('product')) {
        generated.push({ id: '2', type: 'choice', question: 'Do you need to accept payments?', answer: '', options: ['Yes', 'Not yet', 'Free only'] });
        generated.push({ id: '3', type: 'text', question: 'How many products will you start with?', answer: '' });
      } else if (desc.includes('dashboard') || desc.includes('analytics') || desc.includes('data')) {
        generated.push({ id: '2', type: 'choice', question: 'Where does your data come from?', answer: '', options: ['Spreadsheets', 'An API', 'A database', 'Not sure'] });
        generated.push({ id: '3', type: 'text', question: 'What key numbers do you want to see?', answer: '' });
      } else if (desc.includes('blog') || desc.includes('portfolio') || desc.includes('website')) {
        generated.push({ id: '2', type: 'choice', question: 'Do you need a content editor?', answer: '', options: ['Yes', 'No, I\'ll code pages', 'Not sure'] });
        generated.push({ id: '3', type: 'choice', question: 'Do visitors need to sign up?', answer: '', options: ['Yes', 'No', 'Optional'] });
      } else {
        generated.push({ id: '2', type: 'choice', question: 'Do users need to log in?', answer: '', options: ['Yes', 'No', 'Optional'] });
        generated.push({ id: '3', type: 'text', question: 'What is the single most important thing it should do?', answer: '' });
      }

      generated.push({
        id: '4', type: 'choice',
        question: 'Any design preference?',
        answer: '',
        options: ['Clean & minimal', 'Bold & colorful', 'Professional', 'No preference'],
      });

      setQuestions(generated);
      setIsThinking(false);
      setStep('questions');
    }, 1500);
  }, [description]);

  /* ─── File handling ─── */
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected) return;
    const newFiles: UploadedFile[] = Array.from(selected).map(f => ({
      id: Math.random().toString(36).slice(2, 9),
      name: f.name,
      size: f.size,
      type: f.type,
    }));
    setFiles(prev => [...prev, ...newFiles]);
    e.target.value = '';
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  /* ─── Auth entries ─── */
  const addAuth = useCallback(() => {
    setAuths(prev => [...prev, { id: Math.random().toString(36).slice(2, 9), label: '', value: '' }]);
  }, []);

  const removeAuth = useCallback((id: string) => {
    setAuths(prev => prev.filter(a => a.id !== id));
  }, []);

  const updateAuth = useCallback((id: string, field: 'label' | 'value', val: string) => {
    setAuths(prev => prev.map(a => a.id === id ? { ...a, [field]: val } : a));
  }, []);

  /* ─── Submit ─── */
  const handleSubmit = useCallback(() => {
    const name = projectName.trim() || description.slice(0, 40).replace(/[^a-zA-Z0-9 ]/g, '').trim() || 'My Project';
    const qaSummary = questions
      .filter(q => q.answer)
      .map(q => `${q.question}: ${q.answer}`)
      .join('. ');
    const fullDesc = `${description}${qaSummary ? `. Additional details: ${qaSummary}` : ''}`;

    onSubmit({
      name,
      description: fullDesc,
      type: 'Web Application',
      audience: questions.find(q => q.question.includes('Who'))?.answer || 'General',
      services: ['Authentication', 'Database'],
      template: 'blank',
      automationEngine: 'browser-use',
    });
  }, [projectName, description, questions, onSubmit]);

  /* ─── Update question answer ─── */
  const answerQuestion = useCallback((id: string, answer: string) => {
    setQuestions(prev => prev.map(q => q.id === id ? { ...q, answer } : q));
  }, []);

  const allQuestionsAnswered = questions.every(q => q.answer.trim().length > 0);

  /* ═══════════════════════════════════════════
     FILE ICON HELPER
     ═══════════════════════════════════════════ */
  const fileIcon = (type: string) => {
    if (type.startsWith('image/')) return <ImageIcon className="w-4 h-4 text-pink-400" />;
    if (type.includes('pdf')) return <FileText className="w-4 h-4 text-red-400" />;
    return <File className="w-4 h-4 text-blue-400" />;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  /* ═══════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════ */
  return (
    <div className="min-h-full flex items-center justify-center p-4 sm:p-8">
      <div className="w-full max-w-xl space-y-6 animate-fade-in-up">

        {/* ─── Progress dots ─── */}
        <div className="flex items-center justify-center gap-2">
          {['Tell us', 'Clarify', 'Attach', 'Go!'].map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <div className={`flex items-center gap-1.5 transition-all duration-300 ${
                i <= stepIndex ? 'opacity-100' : 'opacity-30'
              }`}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                  i < stepIndex
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : i === stepIndex
                    ? 'bg-primary/20 text-primary border-2 border-primary/40 scale-110'
                    : 'bg-muted/15 text-muted-foreground/50 border border-border/20'
                }`}>
                  {i < stepIndex ? <Check className="w-3 h-3" /> : i + 1}
                </div>
                <span className={`text-[10px] font-medium hidden sm:inline ${
                  i === stepIndex ? 'text-foreground' : 'text-muted-foreground/60'
                }`}>{label}</span>
              </div>
              {i < 3 && <div className={`w-6 h-0.5 rounded-full transition-all ${i < stepIndex ? 'bg-emerald-500/40' : 'bg-border/20'}`} />}
            </div>
          ))}
        </div>

        {/* ═══ STEP 1: DESCRIBE ═══ */}
        {step === 'describe' && (
          <div className="space-y-5">
            <div className="text-center space-y-2">
              <div className="mx-auto w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-3">
                <MessageSquare className="w-6 h-6 text-primary" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-foreground">What do you want to build?</h1>
              <p className="text-sm text-muted-foreground">Describe it in your own words — no technical knowledge needed.</p>
            </div>

            {/* Quick idea chips */}
            <div className="flex flex-wrap items-center justify-center gap-2">
              {QUICK_IDEAS.map(idea => (
                <button
                  key={idea.type}
                  onClick={() => setDescription(prev => prev ? prev : `I want to build an ${idea.label.toLowerCase()}`)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border border-border/30 bg-background/30 text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all"
                >
                  <idea.icon className="w-3 h-3" /> {idea.label}
                </button>
              ))}
            </div>

            {/* Main text input */}
            <div className="relative">
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Example: I want an online store where I can sell handmade jewelry. Customers should be able to browse products, add items to a cart, and pay with a credit card..."
                rows={5}
                className="w-full px-4 py-3 rounded-2xl border border-border/40 bg-background/40 text-sm leading-relaxed outline-none resize-none focus:border-primary/40 focus:ring-2 focus:ring-primary/10 transition-all placeholder:text-muted-foreground/40"
              />
              <div className="absolute bottom-3 right-3 text-[10px] text-muted-foreground/40">
                {description.length}/2000
              </div>
            </div>

            {/* Optional name */}
            <input
              type="text"
              value={projectName}
              onChange={e => setProjectName(e.target.value)}
              placeholder="Project name (optional)"
              className="w-full px-4 py-2.5 rounded-xl border border-border/30 bg-background/30 text-sm outline-none focus:border-primary/30 transition-all placeholder:text-muted-foreground/40"
            />

            <button
              onClick={generateQuestions}
              disabled={description.trim().length < 10 || isThinking}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
              style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))' }}
            >
              {isThinking ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Thinking...</>
              ) : (
                <><Sparkles className="w-4 h-4" /> Continue</>
              )}
            </button>
          </div>
        )}

        {/* ═══ STEP 2: CLARIFYING QUESTIONS ═══ */}
        {step === 'questions' && (
          <div className="space-y-5">
            <div className="text-center space-y-2">
              <h2 className="text-lg font-bold text-foreground">A few quick questions</h2>
              <p className="text-sm text-muted-foreground">This helps us build exactly what you need.</p>
            </div>

            <div className="space-y-4">
              {questions.map(q => (
                <div key={q.id} className="rounded-xl border border-border/30 bg-background/30 p-4 space-y-2.5">
                  <p className="text-sm font-medium text-foreground">{q.question}</p>
                  {q.type === 'choice' && q.options ? (
                    <div className="flex flex-wrap gap-2">
                      {q.options.map(opt => (
                        <button
                          key={opt}
                          onClick={() => answerQuestion(q.id, opt)}
                          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                            q.answer === opt
                              ? 'bg-primary/15 text-primary border border-primary/30'
                              : 'border border-border/30 text-muted-foreground hover:text-foreground hover:border-primary/20'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <input
                      type="text"
                      value={q.answer}
                      onChange={e => answerQuestion(q.id, e.target.value)}
                      placeholder="Type your answer..."
                      className="w-full px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-sm outline-none focus:border-primary/30 transition-all placeholder:text-muted-foreground/40"
                    />
                  )}
                </div>
              ))}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setStep('describe')}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-border/30 text-xs font-medium text-muted-foreground hover:text-foreground transition-all"
              >
                <ArrowLeft className="w-3 h-3" /> Back
              </button>
              <button
                onClick={() => setStep('uploads')}
                disabled={!allQuestionsAnswered}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))' }}
              >
                Continue <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* ═══ STEP 3: UPLOADS & AUTHS ═══ */}
        {step === 'uploads' && (
          <div className="space-y-5">
            <div className="text-center space-y-2">
              <h2 className="text-lg font-bold text-foreground">Anything to attach?</h2>
              <p className="text-sm text-muted-foreground">Upload files, images, or add accounts the app needs to connect to. This step is optional.</p>
            </div>

            {/* File upload area */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Paperclip className="w-3 h-3" /> Files
              </h3>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-6 rounded-xl border-2 border-dashed border-border/30 bg-background/20 text-sm text-muted-foreground hover:text-foreground hover:border-primary/30 transition-all"
              >
                <Upload className="w-4 h-4" /> Drop files or click to upload
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                accept="image/*,.pdf,.doc,.docx,.txt,.csv,.xlsx,.json"
              />
              {files.length > 0 && (
                <div className="space-y-1.5">
                  {files.map(f => (
                    <div key={f.id} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border/20 bg-background/20 text-xs">
                      {fileIcon(f.type)}
                      <span className="flex-1 truncate text-foreground">{f.name}</span>
                      <span className="text-muted-foreground/60">{formatSize(f.size)}</span>
                      <button onClick={() => removeFile(f.id)} className="p-0.5 rounded hover:bg-red-500/10 text-muted-foreground/40 hover:text-red-400 transition-all">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Auth tokens */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Key className="w-3 h-3" /> Accounts & keys <span className="text-muted-foreground/40 font-normal normal-case">(optional)</span>
              </h3>
              <p className="text-[11px] text-muted-foreground/60 leading-relaxed">
                If your app needs to connect to services like Stripe, Google, or a database, add the login info here. We store these securely.
              </p>
              {auths.map(auth => (
                <div key={auth.id} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={auth.label}
                    onChange={e => updateAuth(auth.id, 'label', e.target.value)}
                    placeholder="Service name (e.g. Stripe)"
                    className="flex-1 px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-xs outline-none focus:border-primary/30 transition-all placeholder:text-muted-foreground/40"
                  />
                  <input
                    type="password"
                    value={auth.value}
                    onChange={e => updateAuth(auth.id, 'value', e.target.value)}
                    placeholder="Key or password"
                    className="flex-1 px-3 py-2 rounded-lg border border-border/30 bg-background/20 text-xs outline-none focus:border-primary/30 transition-all placeholder:text-muted-foreground/40"
                  />
                  <button onClick={() => removeAuth(auth.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground/40 hover:text-red-400 transition-all">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
              <button
                onClick={addAuth}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dashed border-border/30 text-xs text-muted-foreground hover:text-foreground hover:border-primary/20 transition-all"
              >
                <Key className="w-3 h-3" /> Add account
              </button>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setStep('questions')}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-border/30 text-xs font-medium text-muted-foreground hover:text-foreground transition-all"
              >
                <ArrowLeft className="w-3 h-3" /> Back
              </button>
              <button
                onClick={() => setStep('confirm')}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98]"
                style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190))' }}
              >
                {files.length === 0 && auths.length === 0 ? 'Skip & Continue' : 'Continue'} <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* ═══ STEP 4: CONFIRM & GO ═══ */}
        {step === 'confirm' && (
          <div className="space-y-5">
            <div className="text-center space-y-2">
              <div className="mx-auto w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-3">
                <Sparkles className="w-6 h-6 text-emerald-400" />
              </div>
              <h2 className="text-lg font-bold text-foreground">Ready to build!</h2>
              <p className="text-sm text-muted-foreground">Here&apos;s a summary of what we&apos;ll create for you.</p>
            </div>

            {/* Summary card */}
            <div className="rounded-xl border border-border/30 bg-background/30 p-4 space-y-3">
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Project</span>
                <p className="text-sm font-medium text-foreground mt-0.5">
                  {projectName || description.slice(0, 60)}
                </p>
              </div>
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Description</span>
                <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed line-clamp-3">{description}</p>
              </div>
              {questions.filter(q => q.answer).length > 0 && (
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Your answers</span>
                  <div className="mt-1 space-y-1">
                    {questions.filter(q => q.answer).map(q => (
                      <div key={q.id} className="flex items-start gap-2 text-xs">
                        <Check className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <span className="text-muted-foreground"><span className="text-foreground/80">{q.question}</span> — {q.answer}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {(files.length > 0 || auths.length > 0) && (
                <div className="flex items-center gap-3 text-[10px] text-muted-foreground pt-1 border-t border-border/20">
                  {files.length > 0 && <span className="flex items-center gap-1"><Paperclip className="w-2.5 h-2.5" /> {files.length} file{files.length > 1 ? 's' : ''}</span>}
                  {auths.length > 0 && <span className="flex items-center gap-1"><Key className="w-2.5 h-2.5" /> {auths.length} account{auths.length > 1 ? 's' : ''}</span>}
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setStep('uploads')}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-border/30 text-xs font-medium text-muted-foreground hover:text-foreground transition-all"
              >
                <ArrowLeft className="w-3 h-3" /> Back
              </button>
              <button
                onClick={handleSubmit}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-bold text-white transition-all hover:scale-[1.02] active:scale-[0.98]"
                style={{ background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190), oklch(0.55 0.18 160))' }}
              >
                <Sparkles className="w-4 h-4" /> Build it for me
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
