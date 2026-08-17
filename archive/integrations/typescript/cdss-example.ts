// Archived proof of concept retained for possible future integration.
import { applyReflectionContext, ReflectionAIClient } from './reflection-ai-client';

const reflection = new ReflectionAIClient({
  baseUrl: process.env.REFLECTION_AI_URL ?? 'http://localhost:8000',
  applicationId: 'cdss',
  tenantId: process.env.REFLECTION_TENANT_ID,
  apiKey: process.env.REFLECTION_AI_API_KEY,
});

// Call immediately before CDSS model routing/provider dispatch.
export async function personalizeCDSSChat(payload: Record<string, any>) {
  const mode = payload.isDims ? 'dims' : payload.isDeepAnalysis ? 'deep_analysis' : 'standard';
  return applyReflectionContext(reflection, payload, {
    mode,
    high_risk: true,
    allow_personalization: mode === 'standard',
    immutable_instructions: ['clinical-safety', 'evidence-and-citation-policy'],
  });
}
