const CLAW_PROTECT_URL = process.env.CLAW_PROTECT_URL || 'http://localhost:3333';

export async function checkPromptInjection(text: string): Promise<{detected: boolean, warnings?: string[]}> {
  try {
    const response = await fetch(`${CLAW_PROTECT_URL}/api/v1/scan/prompt-injection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) return { detected: false };
    return response.json();
  } catch {
    return { detected: false }; // Allow on failure (fail open)
  }
}

export async function scanForSecrets(content: string): Promise<string[]> {
  try {
    const response = await fetch(`${CLAW_PROTECT_URL}/api/v1/scan/secrets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) return [];
    const data = response.json();
    return data.findings || [];
  } catch {
    return [];
  }
}

export async function checkClawProtectHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${CLAW_PROTECT_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}