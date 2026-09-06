/**
 * Landing Hub Client SDK — lphub.ts
 * Tuân thủ Landing Hub Integration Contract v1.0
 * Zero external dependencies — Hoạt động 100% độc lập trong trình duyệt
 */

export interface LPHubConfig {
  projectId: string;
  landingPageId: string;
  apiUrl?: string;
  debug?: boolean;
  autoPageView?: boolean;
}

export interface AttributionTouch {
  utmSource?: string;
  utmMedium?: string;
  utmCampaign?: string;
  utmContent?: string;
  utmTerm?: string;
  referrer?: string;
  landingUrl?: string;
  timestamp?: string;
}

export interface LeadSubmissionPayload {
  formId: string;
  submissionId?: string;
  idempotencyKey?: string;
  name?: string;
  phone?: string;
  email?: string;
  data?: Record<string, any>;
}

export interface OrderCustomer {
  name: string;
  phone: string;
  email?: string;
  address?: string;
  note?: string;
}

export interface OrderItem {
  id?: string;
  name: string;
  quantity: number;
  price: number;
  variant?: string;
}

export interface OrderSubmissionPayload {
  formId: string;
  submissionId?: string;
  idempotencyKey?: string;
  customer: OrderCustomer;
  items: OrderItem[];
  subtotal?: number;
  total: number;
  currency?: string;
  paymentMethod?: string;
  data?: Record<string, any>;
}

export interface CustomFormPayload {
  formId: string;
  submissionId?: string;
  idempotencyKey?: string;
  data: Record<string, any>;
}

export interface ApiResponse<T = any> {
  success: boolean;
  id?: string;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
  };
}

export interface SubmissionSession {
  submissionId: string;
  idempotencyKey: string;
  submitLead(payload: Omit<LeadSubmissionPayload, 'formId' | 'idempotencyKey' | 'submissionId'> & { formId?: string }): Promise<ApiResponse>;
  submitOrder(payload: Omit<OrderSubmissionPayload, 'formId' | 'idempotencyKey' | 'submissionId'> & { formId?: string }): Promise<ApiResponse>;
  submitCustomForm(payload: Omit<CustomFormPayload, 'formId' | 'idempotencyKey' | 'submissionId'> & { formId?: string }): Promise<ApiResponse>;
  reset(): void;
}

class LPHubClient {
  private config: LPHubConfig | null = null;
  private visitorId: string = '';
  private sessionId: string = '';
  private firstTouch: AttributionTouch | null = null;
  private lastTouch: AttributionTouch | null = null;
  private activeSubmissions = new Map<string, { submissionId: string; inFlightPromise?: Promise<ApiResponse> }>();

  constructor() {
    this.initStorage();
  }

  private initStorage() {
    if (typeof window === 'undefined') return;

    // 1. Visitor ID
    try {
      let vid = localStorage.getItem('_lphub_vid');
      if (!vid) {
        vid = 'v_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
        localStorage.setItem('_lphub_vid', vid);
      }
      this.visitorId = vid;
    } catch {
      this.visitorId = 'v_anon_' + Math.random().toString(36).substring(2, 9);
    }

    // 2. Session ID
    try {
      let sid = sessionStorage.getItem('_lphub_sid');
      if (!sid) {
        sid = 's_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
        sessionStorage.setItem('_lphub_sid', sid);
      }
      this.sessionId = sid;
    } catch {
      this.sessionId = 's_anon_' + Math.random().toString(36).substring(2, 9);
    }

    // 3. Attribution
    this.syncAttribution();
  }

  private syncAttribution() {
    if (typeof window === 'undefined') return;

    try {
      const urlParams = new URLSearchParams(window.location.search);
      const utmSource = urlParams.get('utm_source') || undefined;
      const utmMedium = urlParams.get('utm_medium') || undefined;
      const utmCampaign = urlParams.get('utm_campaign') || undefined;
      const utmContent = urlParams.get('utm_content') || undefined;
      const utmTerm = urlParams.get('utm_term') || undefined;
      const referrer = document.referrer || undefined;

      const hasUtm = Boolean(utmSource || utmMedium || utmCampaign || utmContent || utmTerm);

      // Load existing touches
      const storedFt = localStorage.getItem('_lphub_ft');
      if (storedFt) {
        try { this.firstTouch = JSON.parse(storedFt); } catch {}
      }

      const storedLt = localStorage.getItem('_lphub_lt');
      if (storedLt) {
        try { this.lastTouch = JSON.parse(storedLt); } catch {}
      }

      const currentTouch: AttributionTouch = {
        utmSource,
        utmMedium,
        utmCampaign,
        utmContent,
        utmTerm,
        referrer,
        landingUrl: window.location.href,
        timestamp: new Date().toISOString()
      };

      if (!this.firstTouch) {
        this.firstTouch = currentTouch;
        localStorage.setItem('_lphub_ft', JSON.stringify(this.firstTouch));
      }

      if (hasUtm || !this.lastTouch) {
        this.lastTouch = currentTouch;
        localStorage.setItem('_lphub_lt', JSON.stringify(this.lastTouch));
      }
    } catch {}
  }

  public init(config: LPHubConfig) {
    this.config = {
      apiUrl: 'http://localhost:3001',
      debug: false,
      autoPageView: true,
      ...config
    };

    if (this.config.apiUrl?.endsWith('/')) {
      this.config.apiUrl = this.config.apiUrl.slice(0, -1);
    }

    if (this.config.debug) {
      console.log(`[LPHub SDK] Initialized for project=${this.config.projectId}, lp=${this.config.landingPageId}`);
    }

    if (this.config.autoPageView) {
      this.track('page_view');
    }
  }

  private ensureConfigured(): LPHubConfig {
    if (!this.config) {
      throw new Error('[LPHub SDK] LPHub.init() must be called before tracking or submitting.');
    }
    return this.config;
  }

  private getAttributionContext() {
    return {
      visitorId: this.visitorId,
      sessionId: this.sessionId,
      pageUrl: typeof window !== 'undefined' ? window.location.href : '',
      referrer: typeof document !== 'undefined' ? document.referrer : '',
      utmSource: this.lastTouch?.utmSource,
      utmMedium: this.lastTouch?.utmMedium,
      utmCampaign: this.lastTouch?.utmCampaign,
      utmContent: this.lastTouch?.utmContent,
      utmTerm: this.lastTouch?.utmTerm,
      firstTouch: this.firstTouch,
      lastTouch: this.lastTouch
    };
  }

  public async track(eventName: string, metadata?: Record<string, any>): Promise<ApiResponse> {
    const config = this.ensureConfigured();
    const payload = {
      eventName,
      projectId: config.projectId,
      landingPageId: config.landingPageId,
      metadata: metadata || {},
      ...this.getAttributionContext()
    };
    return this.postJson('/api/track', payload);
  }

  public createSubmission(formId: string): SubmissionSession {
    const submissionId = 'ik_sess_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    const self = this;

    return {
      submissionId,
      idempotencyKey: submissionId,
      async submitLead(payload) {
        return self.submitLead({
          ...payload,
          formId: payload.formId || formId,
          submissionId,
          idempotencyKey: submissionId
        });
      },
      async submitOrder(payload) {
        return self.submitOrder({
          ...payload,
          formId: payload.formId || formId,
          submissionId,
          idempotencyKey: submissionId
        });
      },
      async submitCustomForm(payload) {
        return self.submitCustomForm({
          ...payload,
          formId: payload.formId || formId,
          submissionId,
          idempotencyKey: submissionId
        });
      },
      reset() {
        self.activeSubmissions.delete(formId);
      }
    };
  }

  private getOrGenerateKey(formId: string, prefix: string, explicitKey?: string): string {
    if (explicitKey) return explicitKey;
    let entry = this.activeSubmissions.get(formId);
    if (!entry) {
      const key = `${prefix}_${Math.random().toString(36).substring(2, 11)}_${Date.now().toString(36)}`;
      entry = { submissionId: key };
      this.activeSubmissions.set(formId, entry);
    }
    return entry.submissionId;
  }

  private async executeWithDeduplication(
    formId: string,
    key: string,
    operation: () => Promise<ApiResponse>
  ): Promise<ApiResponse> {
    const entry = this.activeSubmissions.get(formId) || { submissionId: key };

    if (entry.inFlightPromise) {
      if (this.config?.debug) {
        console.warn(`[LPHub SDK] In-flight submission joined for formId=${formId}`);
      }
      return entry.inFlightPromise;
    }

    const promise = (async () => {
      try {
        const response = await operation();
        if (response.success) {
          this.activeSubmissions.delete(formId);
        }
        return response;
      } catch (err: any) {
        throw err;
      } finally {
        const current = this.activeSubmissions.get(formId);
        if (current) {
          current.inFlightPromise = undefined;
        }
      }
    })();

    entry.inFlightPromise = promise;
    this.activeSubmissions.set(formId, entry);
    return promise;
  }

  public async submitLead(payload: LeadSubmissionPayload): Promise<ApiResponse> {
    const config = this.ensureConfigured();
    const key = this.getOrGenerateKey(payload.formId, 'ik_lead', payload.idempotencyKey || payload.submissionId);
    const context = this.getAttributionContext();

    return this.executeWithDeduplication(payload.formId, key, async () => {
      const requestBody = {
        projectId: config.projectId,
        landingPageId: config.landingPageId,
        formId: payload.formId,
        submissionId: key,
        idempotencyKey: key,
        name: payload.name,
        phone: payload.phone,
        email: payload.email,
        data: payload.data,
        ...context
      };
      return this.postJson('/api/lead', requestBody);
    });
  }

  public async submitOrder(payload: OrderSubmissionPayload): Promise<ApiResponse> {
    const config = this.ensureConfigured();
    const key = this.getOrGenerateKey(payload.formId, 'ik_ord', payload.idempotencyKey || payload.submissionId);
    const context = this.getAttributionContext();

    return this.executeWithDeduplication(payload.formId, key, async () => {
      const requestBody = {
        projectId: config.projectId,
        landingPageId: config.landingPageId,
        formId: payload.formId,
        submissionId: key,
        idempotencyKey: key,
        customer: payload.customer,
        items: payload.items,
        subtotal: payload.subtotal,
        total: payload.total,
        currency: payload.currency || 'VND',
        paymentMethod: payload.paymentMethod || 'cod',
        data: payload.data,
        ...context
      };
      return this.postJson('/api/order', requestBody);
    });
  }

  public async submitCustomForm(payload: CustomFormPayload): Promise<ApiResponse> {
    const config = this.ensureConfigured();
    const key = this.getOrGenerateKey(payload.formId, 'ik_csub', payload.idempotencyKey || payload.submissionId);
    const context = this.getAttributionContext();

    return this.executeWithDeduplication(payload.formId, key, async () => {
      const requestBody = {
        projectId: config.projectId,
        landingPageId: config.landingPageId,
        formId: payload.formId,
        submissionId: key,
        idempotencyKey: key,
        data: payload.data,
        ...context
      };
      return this.postJson('/api/custom-form', requestBody);
    });
  }

  private async postJson(endpoint: string, data: any): Promise<ApiResponse> {
    const config = this.ensureConfigured();
    const url = `${config.apiUrl}${endpoint}`;

    try {
      if (config.debug) {
        console.log(`[LPHub SDK] POST ${url}:`, data);
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const json = await response.json();
      return json;
    } catch (err: any) {
      console.error(`[LPHub SDK] Network error on ${endpoint}:`, err);
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: err.message || 'Failed to connect to Landing Hub API'
        }
      };
    }
  }

  public getVisitorId(): string { return this.visitorId; }
  public getSessionId(): string { return this.sessionId; }
}

export const LPHub = new LPHubClient();
if (typeof window !== 'undefined') {
  (window as any).LPHub = LPHub;
}
