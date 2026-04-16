import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

// Workspace root — prefer env var, fallback to relative path
const WORKFORCE_ROOT = process.env.WORKFORCE_ROOT ?? path.resolve(process.cwd(), '..', '..');

// Default venture catalog if file doesn't exist
const DEFAULT_CATALOG = {
  ventures: [
    { id: 'alpha_engine', name: 'AlphaEngine', status: 'scaffolded' },
    { id: 'course_factory', name: 'CourseFactory', status: 'scaffolded' },
    { id: 'visual_workflow_studio', name: 'VisualWorkflowStudio', status: 'scaffolded' },
    { id: 'research_to_revenue', name: 'ResearchToRevenue', status: 'scaffolded' },
    { id: 'self_healing_mesh', name: 'SelfHealingMesh', status: 'scaffolded' },
  ],
  combo_chains: [],
};

export async function GET() {
  try {
    // Sanitize path and ensure it doesn't escape workspace
    const catalogPath = path.join(WORKFORCE_ROOT, 'venture-catalog.json');
    const normalizedPath = path.normalize(catalogPath);
    
    // Safety check: ensure path is within expected root
    if (!normalizedPath.startsWith(path.normalize(WORKFORCE_ROOT))) {
      console.warn('Catalog path escaped workspace root');
      return NextResponse.json(DEFAULT_CATALOG);
    }
    
    const data = await fs.readFile(normalizedPath, 'utf-8');
    return NextResponse.json(JSON.parse(data));
  } catch {
    // Fallback: return default catalog if file not found
    return NextResponse.json(DEFAULT_CATALOG);
  }
}
