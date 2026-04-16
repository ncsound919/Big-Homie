/**
 * Centralised icon map – maps simple name strings to lucide-react components.
 * Use <AppIcon name="xxx" className="..." /> everywhere instead of
 * <i className="fa-solid fa-xxx" />.
 */
import {
  AlignLeft,
  Atom,
  BarChart2,
  Bolt,
  Bot,
  Box,
  Boxes,
  Brain,
  Bug,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Chrome,
  Circle,
  ClipboardCheck,
  Clock,
  Cloud,
  Code2,
  Compass,
  Container,
  Cpu,
  Database,
  Dot,
  Eye,
  File,
  FileCode2,
  FileText,
  Flame,
  FlaskConical,
  Gauge,
  Gem,
  GitBranch,
  GitMerge,
  Globe,
  Hand,
  Hexagon,
  Info,
  Inbox,
  Layout,
  Layers,
  LayoutDashboard,
  Link,
  ListChecks,
  List,
  Loader2,
  Lock,
  MessageSquare,
  Minus,
  Monitor,
  Moon,
  MousePointer2,
  Network,
  Package2,
  PartyPopper,
  PenLine,
  PieChart,
  Play,
  Plug,
  Plus,
  Puzzle,
  Radio,
  Rocket,
  Route,
  Scan,
  Search,
  Server,
  Shield,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Star,
  Sun,
  Terminal,
  TestTube,
  TrendingUp,
  TriangleAlert,
  Unplug,
  Users,
  Wand2,
  Wind,
  Workflow,
  Wrench,
  X,
  XCircle,
  Zap,
  type LucideProps,
} from 'lucide-react';
import type { ComponentType } from 'react';

// Map from simple icon-name to lucide component
const iconMap: Record<string, ComponentType<LucideProps>> = {
  // navigation / UI
  'chevron-right': ChevronRight,
  'chevron-down': ChevronDown,
  'plus': Plus,
  'minus': Minus,
  'x': X,
  'search': Search,
  'moon': Moon,
  'sun': Sun,

  // status
  'circle': Circle,
  'loader': Loader2,
  'check': Check,
  'check-check': CheckCheck,
  'check-circle': CheckCircle2,
  'x-circle': XCircle,
  'info': Info,
  'inbox': Inbox,

  // project / pipeline
  'brain': Brain,
  'message-square': MessageSquare,
  'compass': Compass,
  'layers': Layers,
  'boxes': Boxes,
  'gauge': Gauge,
  'shield': Shield,
  'shield-check': ShieldCheck,
  'route': Route,
  'play': Play,
  'rocket': Rocket,
  'party-popper': PartyPopper,
  'layout-dashboard': LayoutDashboard,
  'hexagon': Hexagon,

  // code / audit
  'code': Code2,
  'file-code': FileCode2,
  'gem': Gem,
  'lock': Lock,
  'cpu': Cpu,
  'flask': FlaskConical,
  'test-tube': TestTube,
  'wrench': Wrench,
  'workflow': Workflow,
  'git-branch': GitBranch,
  'zap': Zap,

  // form / content
  'file': File,
  'file-text': FileText,
  'pen-line': PenLine,
  'align-left': AlignLeft,
  'puzzle': Puzzle,
  'list': List,
  'list-checks': ListChecks,
  'clipboard-check': ClipboardCheck,

  // tech / stack
  'cloud': Cloud,
  'server': Server,
  'database': Database,
  'network': Network,
  'wind': Wind,
  'atom': Atom,
  'package': Package2,
  'box': Box,
  'globe': Globe,

  // charts
  'trending-up': TrendingUp,
  'bar-chart': BarChart2,
  'pie-chart': PieChart,

  // people
  'users': Users,
  'shopping-cart': ShoppingCart,

  // misc
  'clock': Clock,
  'triangle-alert': TriangleAlert,
  'dot': Dot,
  'bolt': Bolt,

  // browser automation / tools
  'bot': Bot,
  'bug': Bug,
  'chrome': Chrome,
  'container': Container,
  'eye': Eye,
  'flame': Flame,
  'git-merge': GitMerge,
  'hand': Hand,
  'layout': Layout,
  'link': Link,
  'monitor': Monitor,
  'mouse-pointer': MousePointer2,
  'plug': Plug,
  'radio': Radio,
  'scan': Scan,
  'sparkles': Sparkles,
  'star': Star,
  'terminal': Terminal,
  'unplug': Unplug,
  'wand': Wand2,
};

interface AppIconProps extends LucideProps {
  name: string;
}

/**
 * Renders the lucide-react icon for the given `name`.
 * Falls back to a <Dot /> if the name is unknown.
 */
export function AppIcon({ name, ...props }: AppIconProps) {
  const Icon = iconMap[name] ?? Dot;
  return <Icon {...props} />;
}
