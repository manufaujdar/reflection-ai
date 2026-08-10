// Archived integration prototype. Not part of the active standalone product surface.
export type ReflectionApplication = 'cdss' | 'masterllm' | (string & {});

export interface ReflectionClientOptions {
  baseUrl: string;
  applicationId: ReflectionApplication;
  tenantId?: string;
  apiKey?: string;
  timeoutMs?: number;
}

export interface HostSafetyContext {
  mode?: 'standard' | 'deep_analysis' | 'dims' | 'clinical_protocol' | 'emergency' | string;
  high_risk?: boolean;
  allow_personalization?: boolean;
  immutable_instructions?: string[];
}

export interface ReflectionContext {
  subject_id: string;
  profile_version: number;
  personalization_applied: boolean;
  personalization_reason: string;
  prompt: {
    system_prompt: string;
    system_prompt_addendum: string;
    instructions: string[];
  };
  preferences: Record<string, unknown>;
  routing_hints: Record<string, unknown>;
  trace: Record<string, unknown>;
}

export interface ExistingChatRequest {
  input?: string;
  prompt?: string;
  model?: string;
  sessionId?: string;
  userId?: string;
  messages?: Array<{ role: string; content: string }>;
  personalization?: Record<string, unknown>;
  memoryContext?: string;
  feedbackAnalysis?: Record<string, unknown>;
  systemPrompt?: string;
  [key: string]: unknown;
}

export class ReflectionAIClient {
  private readonly baseUrl: string;
  private readonly tenantId: string;

  constructor(private readonly options: ReflectionClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.tenantId = options.tenantId ?? 'default';
  }

  private async request<T>(path: string, body: unknown): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.options.timeoutMs ?? 1500);
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          ...(this.options.apiKey ? { authorization: `Bearer ${this.options.apiKey}` } : {}),
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`Reflection AI returned ${response.status}`);
      return (await response.json()) as T;
    } finally {
      clearTimeout(timeout);
    }
  }

  async resolveSubject(externalUserId: string, consent: boolean, trainingConsent = false) {
    return this.request<{ id: string }>('/v1/subjects/resolve', {
      application_id: this.options.applicationId,
      tenant_id: this.tenantId,
      external_id: externalUserId,
      consent,
      training_consent: trainingConsent,
    });
  }

  async getContext(
    externalUserId: string,
    chat: ExistingChatRequest,
    safety: HostSafetyContext = {},
  ): Promise<ReflectionContext> {
    return this.request<ReflectionContext>('/v1/context', {
      application_id: this.options.applicationId,
      tenant_id: this.tenantId,
      external_user_id: externalUserId,
      session_id: chat.sessionId,
      request_id: crypto.randomUUID(),
      base_system_prompt: chat.systemPrompt,
      host_personalization: chat.personalization ?? {},
      memory_context: chat.memoryContext,
      feedback_analysis: chat.feedbackAnalysis ?? {},
      safety,
    });
  }

  async captureEvent(
    subjectId: string,
    event: {
      kind: 'interaction' | 'feedback' | 'preference' | 'correction';
      idempotencyKey: string;
      sessionId?: string;
      messageId?: string;
      model?: string;
      inputText?: string;
      outputText?: string;
      feedback?: number;
      attributes?: Record<string, unknown>;
    },
  ): Promise<void> {
    await this.request(`/v1/users/${subjectId}/events`, {
      kind: event.kind,
      idempotency_key: event.idempotencyKey,
      session_id: event.sessionId,
      message_id: event.messageId,
      model: event.model,
      input_text: event.inputText,
      output_text: event.outputText,
      feedback: event.feedback,
      attributes: event.attributes ?? {},
      source: this.options.applicationId,
    });
  }
}

/**
 * Fail-open adapter for the existing CDSS/MasterLLM ChatRequest contract.
 * Safety and model execution remain owned by the host application.
 */
export async function applyReflectionContext(
  client: ReflectionAIClient,
  request: ExistingChatRequest,
  safety: HostSafetyContext = {},
): Promise<ExistingChatRequest> {
  if (!request.userId) return request;
  try {
    const context = await client.getContext(request.userId, request, safety);
    return {
      ...request,
      systemPrompt: context.prompt.system_prompt,
      personalization: { ...request.personalization, ...context.preferences },
      reflectionContext: context.trace,
    };
  } catch {
    return request;
  }
}
