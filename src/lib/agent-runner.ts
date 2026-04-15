import { securityMiddleware } from './security-middleware';
import type { CustomAgent } from '@/types/agent';

interface AgentContext extends CustomAgent {
  config?: object;
  code?: string;
}

interface AgentAction {
  action: string;
  params: Record<string, unknown>;
}

export async function runAgent(
  context: AgentContext,
  action: string,
  params: Record<string, unknown>
): Promise<{ success: boolean; result?: unknown; error?: string }> {
  let shouldValidate = true;
  let validationLevel = 'full';

  if (context.securityTier === 'reduced') {
    shouldValidate = true;
    validationLevel = 'reduced';
  } else if (context.securityTier === 'custom') {
    shouldValidate = true;
    validationLevel = 'full';
  }

  if (shouldValidate) {
    const validationParams = {
      ...params,
      _tier: validationLevel,
    };

    const result = await securityMiddleware.validateAction(action, validationParams);

    if (!result.approved) {
      return {
        success: false,
        error: `Security blocked: ${result.blockedReasons.join(', ')}`,
      };
    }
  }

  return { success: true, result: { message: 'Agent executed successfully' } };
}

export const agentRunner = {
  runAgent,
};