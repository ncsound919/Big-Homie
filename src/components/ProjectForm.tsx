'use client';

import { useState, useEffect } from 'react';
import { AppIcon } from '@/lib/icons';
import AutomationEngineSelector from './AutomationEngineSelector';

export interface ProjectData {
  name: string;
  description: string;
  type: string;
  audience: string;
  services: string[];
  template: string;
  automationEngine: string;
  // New enhanced fields
  techStack?: {
    frontend?: string[];
    backend?: string[];
    database?: string;
    styling?: string;
  };
  features?: string[];
  designPreferences?: {
    theme?: string;
    colorScheme?: string;
    layout?: string;
    typography?: string;
  };
  customRequirements?: string;
}

interface ProjectFormProps {
  onSubmit: (data: ProjectData) => void;
  isAnalyzing: boolean;
}

const TEMPLATES = [
  { id: 'blank', name: 'Blank Project', icon: 'file', desc: 'Start from scratch' },
  { id: 'saas', name: 'SaaS Starter', icon: 'cloud', desc: 'Multi-tenant app with billing' },
  { id: 'ecommerce', name: 'E-Commerce', icon: 'shopping-cart', desc: 'Online store with payments' },
  { id: 'dashboard', name: 'Dashboard', icon: 'trending-up', desc: 'Analytics & monitoring' },
  { id: 'web-scraper', name: 'Web Scraper', icon: 'scan', desc: 'Structured data extraction' },
  { id: 'browser-testing', name: 'Browser Testing', icon: 'monitor', desc: 'Cross-browser test suite' },
  { id: 'workflow-bot', name: 'Workflow Bot', icon: 'bot', desc: 'Automated browser workflows' },
  { id: 'visual-testing', name: 'Visual Testing', icon: 'eye', desc: 'Screenshot & regression tests' },
  { id: 'api', name: 'API Backend', icon: 'server', desc: 'REST/GraphQL API service' },
  { id: 'portfolio', name: 'Portfolio', icon: 'image', desc: 'Personal portfolio site' },
  { id: 'blog', name: 'Blog / CMS', icon: 'file-text', desc: 'Content management blog' },
  { id: 'landing-page', name: 'Landing Page', icon: 'layout', desc: 'Marketing landing page' },
  { id: 'mobile-app', name: 'PWA / Mobile', icon: 'smartphone', desc: 'Progressive web app' },
  { id: 'admin-panel', name: 'Admin Panel', icon: 'settings', desc: 'Backend admin dashboard' },
];

const PROJECT_TYPES = [
  'Web Application',
  'Browser Automation',
  'Web Scraping',
  'Cross-Browser Testing',
  'Visual Regression Testing',
  'Workflow Automation',
  'API / Microservice',
  'CLI Tool',
  'Browser Extension',
  'Library / SDK',
  'Mobile App (PWA)',
  'Static Website',
];

const SERVICES = [
  'Authentication',
  'Database',
  'File Storage',
  'Email',
  'Payments',
  'Search',
  'Real-time',
  'Analytics',
  'Notifications',
  'Caching',
  'CAPTCHA Solving',
  'Proxy Rotation',
  'Screenshot Capture',
  'PDF Generation',
  'AI/ML Integration',
  'Social Media Integration',
  'SEO Optimization',
  'Multi-language',
];

// Tech stack options
const FRONTEND_OPTIONS = ['React', 'Vue', 'Angular', 'Next.js', 'Svelte', 'Vanilla JS', 'Alpine.js', 'Solid', 'Remix'];
const BACKEND_OPTIONS = ['Node.js', 'Python/Django', 'Python/FastAPI', 'Go', 'Rust', 'PHP/Laravel', 'Ruby on Rails', 'Java Spring', '.NET'];
const DATABASE_OPTIONS = ['PostgreSQL', 'MySQL', 'MongoDB', 'SQLite', 'Redis', 'Supabase', 'Firebase', 'Prisma', 'Neon'];
const STYLING_OPTIONS = ['Tailwind CSS', 'Bootstrap', 'Material UI', 'Chakra UI', 'Framer Motion', 'Styled Components', 'CSS Modules', 'Plain CSS', 'SCSS'];

// Template-specific features
const TEMPLATE_FEATURES: Record<string, string[]> = {
  saas: ['User Authentication', 'Multi-tenancy', 'Subscription Billing', 'Team Management', 'Role-based Access', 'API Webhooks', 'Email Notifications', 'Invoice Generation', 'Analytics Dashboard', 'Onboarding Flow'],
  ecommerce: ['Product Catalog', 'Shopping Cart', 'Checkout Flow', 'Payment Processing', 'Order Management', 'Inventory Tracking', 'Customer Accounts', 'Wishlist', 'Product Reviews', 'Coupon Codes', 'Shipping Integration', 'Tax Calculation'],
  dashboard: ['Data Visualization', 'Charts & Graphs', 'Real-time Updates', 'Data Export', 'Filter & Search', 'Date Range Picker', 'Dark/Light Mode', 'Responsive Layout', 'Custom Widgets', 'Report Generation'],
  'web-scraper': ['Rate Limiting', 'Data Export (CSV/JSON)', 'Scheduled Runs', 'Proxy Rotation', 'Error Handling', 'Data Cleaning', 'Dynamic Content', 'Pagination Handling', 'Authentication Handling', 'Cloud Storage'],
  'browser-testing': ['Cross-browser Tests', 'Screenshot Comparison', 'Visual Regression', 'Mobile Emulation', 'Network Throttling', 'Console Error Tracking', 'Performance Metrics', 'Accessibility Tests', 'Test Scheduling', 'CI/CD Integration'],
  'workflow-bot': ['Task Scheduling', 'Form Filling', 'Data Entry', 'Report Generation', 'Email Automation', 'Webhook Triggers', 'Retry Logic', 'State Management', 'Conditional Logic', 'Notification Alerts'],
  api: ['REST API', 'GraphQL', 'Authentication (JWT)', 'Rate Limiting', 'Input Validation', 'Error Handling', 'API Documentation', 'Pagination', 'Caching', 'WebSockets'],
  portfolio: ['Hero Section', 'About Page', 'Projects Gallery', 'Blog Section', 'Contact Form', 'Resume Download', 'Social Links', 'Dark/Light Toggle', 'Animations', 'SEO Meta Tags'],
  blog: ['Markdown Support', 'Categories & Tags', 'Search Functionality', 'Comment System', 'Newsletter Signup', 'Social Sharing', 'Reading Time', 'Related Posts', 'Sitemap', 'RSS Feed'],
  'landing-page': ['Hero Section', 'Features Grid', 'Testimonials', 'Pricing Table', 'FAQ Section', 'Contact Form', 'CTA Buttons', 'Video Embed', 'Countdown Timer', 'Animated Sections'],
  'mobile-app': ['PWA Support', 'Offline Mode', 'Push Notifications', 'Camera Access', 'Geolocation', 'Offline Storage', 'Install Prompt', 'App Shell', 'Lazy Loading', 'Touch Gestures'],
  'admin-panel': ['User Management', 'CRUD Operations', 'Data Tables', 'File Upload', 'Settings Page', 'Activity Logs', 'Audit Trail', 'Export Options', 'Bulk Actions', 'Drag & Drop'],
};

const THEMES = ['Modern', 'Dark Mode', 'Light Mode', 'Glassmorphism', 'Neumorphism', 'Minimalist', 'Cyberpunk', 'Retro', 'Nature-inspired', 'Corporate'];
const COLOR_SCHEMES = ['Blue', 'Purple', 'Green', 'Orange', 'Red', 'Teal', 'Pink', 'Monochrome', 'Gradient', 'Custom'];
const LAYOUTS = ['Single Page', 'Multi-page', 'Sidebar Navigation', 'Top Navigation', 'Grid-based', 'Masonry', 'Full-width', 'Boxed', 'Sticky Header'];

export default function ProjectForm({ onSubmit, isAnalyzing }: ProjectFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState('Web Application');
  const [audience, setAudience] = useState('');
  const [services, setServices] = useState<string[]>(['Authentication', 'Database']);
  const [template, setTemplate] = useState('blank');
  const [automationEngine, setAutomationEngine] = useState('playwright');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showTechStack, setShowTechStack] = useState(false);
  const [showDesign, setShowDesign] = useState(false);
  
  // New enhanced state
  const [techStack, setTechStack] = useState({
    frontend: ['React'],
    backend: ['Node.js'],
    database: 'PostgreSQL',
    styling: 'Tailwind CSS',
  });
  
  const [features, setFeatures] = useState<string[]>([]);
  const [designPreferences, setDesignPreferences] = useState({
    theme: 'Modern',
    colorScheme: 'Blue',
    layout: 'Single Page',
  });
  const [customRequirements, setCustomRequirements] = useState('');

  // Update features when template changes
  useEffect(() => {
    if (TEMPLATE_FEATURES[template]) {
      setFeatures(TEMPLATE_FEATURES[template].slice(0, 5)); // Default to first 5 features
    } else {
      setFeatures([]);
    }
  }, [template]);

  const toggleService = (service: string) => {
    setServices((prev) =>
      prev.includes(service) ? prev.filter((s) => s !== service) : [...prev, service]
    );
  };

  const toggleFeature = (feature: string) => {
    setFeatures((prev) =>
      prev.includes(feature) ? prev.filter((f) => f !== feature) : [...prev, feature]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !description.trim()) return;
    onSubmit({ 
      name, 
      description, 
      type, 
      audience, 
      services, 
      template, 
      automationEngine,
      techStack,
      features,
      designPreferences,
      customRequirements,
    });
  };

  // Get available features for current template
  const availableFeatures = TEMPLATE_FEATURES[template] || [];

  return (
    <div className="w-full max-w-3xl mx-auto animate-fade-in-up">
      <div className="glass-strong rounded-2xl p-6 sm:p-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-purple-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            Create New Project
          </h2>
          <p className="text-muted-foreground mt-2 text-sm">
            Define your project and let AI build it autonomously
          </p>
        </div>

        {/* Template Selection - More Options */}
        <div className="mb-6">
          <label className="text-sm font-medium text-foreground mb-3 block">
            <AppIcon name="layers" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
            Project Template
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {TEMPLATES.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => {
                  setTemplate(t.id);
                  if (t.id === 'saas') {
                    setServices(['Authentication', 'Database', 'Payments', 'Email']);
                    setType('Web Application');
                  } else if (t.id === 'ecommerce') {
                    setServices(['Database', 'Payments', 'File Storage', 'Search']);
                    setType('Web Application');
                  } else if (t.id === 'dashboard') {
                    setServices(['Authentication', 'Database', 'Analytics', 'Real-time']);
                    setType('Web Application');
                  } else if (t.id === 'web-scraper') {
                    setServices(['Database', 'Proxy Rotation', 'Caching']);
                    setType('Web Scraping');
                    setAutomationEngine('puppeteer');
                  } else if (t.id === 'browser-testing') {
                    setServices(['Screenshot Capture', 'Analytics', 'Notifications']);
                    setType('Cross-Browser Testing');
                    setAutomationEngine('playwright');
                  } else if (t.id === 'workflow-bot') {
                    setServices(['Authentication', 'CAPTCHA Solving', 'Proxy Rotation', 'Notifications']);
                    setType('Workflow Automation');
                    setAutomationEngine('skyvern');
                  } else if (t.id === 'visual-testing') {
                    setServices(['Screenshot Capture', 'File Storage', 'Notifications']);
                    setType('Visual Regression Testing');
                    setAutomationEngine('playwright');
                  } else if (t.id === 'api') {
                    setServices(['Authentication', 'Database', 'Caching']);
                    setType('API / Microservice');
                  } else if (t.id === 'portfolio') {
                    setServices(['File Storage', 'Email']);
                    setType('Static Website');
                  } else if (t.id === 'blog') {
                    setServices(['Database', 'Email', 'Search']);
                    setType('Web Application');
                  } else if (t.id === 'landing-page') {
                    setServices(['Email', 'Notifications']);
                    setType('Static Website');
                  } else if (t.id === 'mobile-app') {
                    setServices(['Database', 'Notifications', 'File Storage']);
                    setType('Mobile App (PWA)');
                  } else if (t.id === 'admin-panel') {
                    setServices(['Authentication', 'Database', 'File Storage']);
                    setType('Web Application');
                  }
                }}
                className={`p-3 rounded-xl border text-left transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] ${
                  template === t.id
                    ? 'border-primary/50 bg-primary/10 shadow-sm glow-purple'
                    : 'border-border/50 bg-background/30 hover:border-primary/30 hover:bg-primary/5'
                }`}
              >
                <AppIcon name={t.icon} className="w-5 h-5 text-primary mb-1.5" />
                <p className="text-xs font-medium text-foreground">{t.name}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{t.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Project Name */}
          <div>
            <label htmlFor="project-name" className="text-sm font-medium text-foreground mb-1.5 block">
              <AppIcon name="pen-line" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
              Project Name *
            </label>
            <input
              id="project-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Awesome Project"
              className="w-full px-4 py-2.5 rounded-xl border border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all duration-200 text-sm"
              required
            />
          </div>

          {/* Description - More detailed */}
          <div>
            <label htmlFor="project-desc" className="text-sm font-medium text-foreground mb-1.5 block">
              <AppIcon name="align-left" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
              Description *
            </label>
            <textarea
              id="project-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what your project does, its main features, target users, and specific requirements. Be as detailed as possible..."
              rows={4}
              className="w-full px-4 py-2.5 rounded-xl border border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all duration-200 text-sm resize-none"
              required
            />
          </div>

          {/* Project Type & Audience */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="project-type" className="text-sm font-medium text-foreground mb-1.5 block">
                <AppIcon name="layers" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
                Project Type
              </label>
              <select
                id="project-type"
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-border/50 bg-background/50 text-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all duration-200 text-sm"
              >
                {PROJECT_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="project-audience" className="text-sm font-medium text-foreground mb-1.5 block">
                <AppIcon name="users" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
                Target Audience
              </label>
              <input
                id="project-audience"
                type="text"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                placeholder="e.g., developers, small businesses"
                className="w-full px-4 py-2.5 rounded-xl border border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all duration-200 text-sm"
              />
            </div>
          </div>

          {/* Features Selection (if template has features) */}
          {availableFeatures.length > 0 && (
            <div>
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors mb-2"
              >
                <AppIcon name="chevron-right" className={`w-3 h-3 transition-transform duration-200 ${showAdvanced ? 'rotate-90' : ''}`} />
                <AppIcon name="zap" className="w-3.5 h-3.5 text-primary" />
                Key Features to Include
                <span className="text-xs text-muted-foreground">({features.length} selected)</span>
              </button>
              {showAdvanced && (
                <div className="flex flex-wrap gap-2 animate-fade-in-up">
                  {availableFeatures.map((feature) => (
                    <button
                      key={feature}
                      type="button"
                      onClick={() => toggleFeature(feature)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 hover:scale-105 active:scale-95 ${
                        features.includes(feature)
                          ? 'bg-primary/20 text-primary border border-primary/30'
                          : 'bg-muted/50 text-muted-foreground border border-border/50 hover:border-primary/20 hover:text-foreground'
                      }`}
                    >
                      {feature}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tech Stack Selection */}
          <div>
            <button
              type="button"
              onClick={() => setShowTechStack(!showTechStack)}
              className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors mb-2"
            >
              <AppIcon name="chevron-right" className={`w-3 h-3 transition-transform duration-200 ${showTechStack ? 'rotate-90' : ''}`} />
              <AppIcon name="code" className="w-3.5 h-3.5 text-primary" />
              Tech Stack (Optional)
            </button>
            {showTechStack && (
              <div className="space-y-4 p-4 bg-muted/20 rounded-xl animate-fade-in-up">
                {/* Frontend */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Frontend</label>
                  <div className="flex flex-wrap gap-2">
                    {FRONTEND_OPTIONS.map((fw) => (
                      <button
                        key={fw}
                        type="button"
                        onClick={() => setTechStack(prev => ({
                          ...prev,
                          frontend: prev.frontend?.includes(fw) 
                            ? prev.frontend.filter(f => f !== fw)
                            : [...(prev.frontend || []), fw]
                        }))}
                        className={`px-2 py-1 rounded text-xs ${
                          techStack.frontend?.includes(fw)
                            ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                            : 'bg-muted/50 text-muted-foreground border border-border/50'
                        }`}
                      >
                        {fw}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Backend */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Backend</label>
                  <div className="flex flex-wrap gap-2">
                    {BACKEND_OPTIONS.map((bw) => (
                      <button
                        key={bw}
                        type="button"
                        onClick={() => setTechStack(prev => ({
                          ...prev,
                          backend: prev.backend?.includes(bw)
                            ? prev.backend.filter(b => b !== bw)
                            : [...(prev.backend || []), bw]
                        }))}
                        className={`px-2 py-1 rounded text-xs ${
                          techStack.backend?.includes(bw)
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                            : 'bg-muted/50 text-muted-foreground border border-border/50'
                        }`}
                      >
                        {bw}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Database */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Database</label>
                  <select
                    value={techStack.database}
                    onChange={(e) => setTechStack(prev => ({ ...prev, database: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-border/50 bg-background/50 text-sm"
                  >
                    {DATABASE_OPTIONS.map((db) => (
                      <option key={db} value={db}>{db}</option>
                    ))}
                  </select>
                </div>
                
                {/* Styling */}
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Styling</label>
                  <div className="flex flex-wrap gap-2">
                    {STYLING_OPTIONS.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setTechStack(prev => ({ ...prev, styling: s }))}
                        className={`px-2 py-1 rounded text-xs ${
                          techStack.styling === s
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-muted/50 text-muted-foreground border border-border/50'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Design Preferences */}
          <div>
            <button
              type="button"
              onClick={() => setShowDesign(!showDesign)}
              className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors mb-2"
            >
              <AppIcon name="chevron-right" className={`w-3 h-3 transition-transform duration-200 ${showDesign ? 'rotate-90' : ''}`} />
              <AppIcon name="palette" className="w-3.5 h-3.5 text-primary" />
              Design Preferences (Optional)
            </button>
            {showDesign && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 bg-muted/20 rounded-xl animate-fade-in-up">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Theme</label>
                  <select
                    value={designPreferences.theme}
                    onChange={(e) => setDesignPreferences(prev => ({ ...prev, theme: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-border/50 bg-background/50 text-sm"
                  >
                    {THEMES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Color Scheme</label>
                  <select
                    value={designPreferences.colorScheme}
                    onChange={(e) => setDesignPreferences(prev => ({ ...prev, colorScheme: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-border/50 bg-background/50 text-sm"
                  >
                    {COLOR_SCHEMES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-2 block">Layout</label>
                  <select
                    value={designPreferences.layout}
                    onChange={(e) => setDesignPreferences(prev => ({ ...prev, layout: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-border/50 bg-background/50 text-sm"
                  >
                    {LAYOUTS.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Services - Collapsible */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors mb-2"
            >
              <AppIcon name="chevron-right" className={`w-3 h-3 transition-transform duration-200 ${showAdvanced ? 'rotate-90' : ''}`} />
              <AppIcon name="puzzle" className="w-3.5 h-3.5 text-primary" />
              Services & Integrations
              <span className="text-xs text-muted-foreground">({services.length} selected)</span>
            </button>
            {showAdvanced && (
              <div className="flex flex-wrap gap-2 animate-fade-in-up">
                {SERVICES.map((service) => (
                  <button
                    key={service}
                    type="button"
                    onClick={() => toggleService(service)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 hover:scale-105 active:scale-95 ${
                      services.includes(service)
                        ? 'bg-primary/20 text-primary border border-primary/30'
                        : 'bg-muted/50 text-muted-foreground border border-border/50 hover:border-primary/20 hover:text-foreground'
                    }`}
                  >
                    {service}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Custom Requirements */}
          <div>
            <label htmlFor="custom-req" className="text-sm font-medium text-foreground mb-1.5 block">
              <AppIcon name="list-ordered" className="inline-block w-3.5 h-3.5 mr-1.5 text-primary" />
              Custom Requirements (Optional)
            </label>
            <textarea
              id="custom-req"
              value={customRequirements}
              onChange={(e) => setCustomRequirements(e.target.value)}
              placeholder="Any specific requirements, constraints, or preferences not covered above..."
              rows={2}
              className="w-full px-4 py-2.5 rounded-xl border border-border/50 bg-background/50 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all duration-200 text-sm resize-none"
            />
          </div>

          {/* Automation Engine */}
          <AutomationEngineSelector
            selectedEngine={automationEngine}
            onSelect={setAutomationEngine}
          />

          {/* Submit */}
          <button
            type="submit"
            disabled={!name.trim() || !description.trim() || isAnalyzing}
            className="w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            style={{
              background: 'linear-gradient(135deg, oklch(0.55 0.22 280), oklch(0.6 0.2 190), oklch(0.55 0.18 160))',
              color: 'white',
            }}
          >
            {isAnalyzing ? (
              <span className="flex items-center justify-center gap-2">
                <AppIcon name="loader" className="w-4 h-4 animate-spin" />
                AI is analyzing your project...
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <AppIcon name="rocket" className="w-4 h-4" />
                Launch Project Build
              </span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
