import React, { useEffect, useRef, useState } from 'react';
import { LPHub } from '../lib/lphub';
import type { FormContent, FormField, SiteContent } from '../types/content';
import { Text } from './Text';

const CUSTOMER_KEYS = ['name', 'phone', 'email', 'address', 'note'];

const FieldControl: React.FC<{ f: FormField; value: string; onChange: (v: string) => void; onFocus: () => void }> = ({
  f,
  value,
  onChange,
  onFocus,
}) => {
  const common = {
    id: `f_${f.key}`,
    name: f.key,
    required: f.required,
    value,
    onFocus,
    className: 'field-input',
    'aria-describedby': `e_${f.key}`,
  };
  if (f.type === 'textarea') {
    return <textarea {...common} rows={3} placeholder={f.placeholder} onChange={(e) => onChange(e.target.value)} />;
  }
  if (f.type === 'select') {
    return (
      <select {...common} onChange={(e) => onChange(e.target.value)}>
        <option value="">{f.placeholder ?? '-- Chọn --'}</option>
        {f.options?.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      {...common}
      type={f.type}
      inputMode={f.type === 'tel' ? 'tel' : f.type === 'number' ? 'numeric' : undefined}
      autoComplete={f.key === 'name' ? 'name' : f.key === 'phone' ? 'tel' : f.key === 'email' ? 'email' : f.key === 'address' ? 'street-address' : 'off'}
      pattern={f.type === 'tel' ? '[0-9 +().-]{8,15}' : undefined}
      min={f.min}
      max={f.max}
      placeholder={f.placeholder}
      onChange={(e) => onChange(e.target.value)}
    />
  );
};

export const LandingForm: React.FC<{ form: FormContent; hub: SiteContent['hub'] }> = ({ form, hub }) => {
  const [values, setValues] = useState<Record<string, string>>({});
  const [quantity, setQuantity] = useState(1);
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [errorDetail, setErrorDetail] = useState('');
  const started = useRef(false);
  const sectionRef = useRef<HTMLElement>(null);
  const session = useRef(LPHub.createSubmission(hub.formId));

  useEffect(() => {
    const el = sectionRef.current;
    if (!el || !('IntersectionObserver' in window)) return;
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        LPHub.track('form_view', { formId: hub.formId, section: form.id });
        io.disconnect();
      }
    });
    io.observe(el);
    return () => io.disconnect();
  }, [hub.formId, form.id]);

  const onFocus = (key: string) => {
    if (started.current) return;
    started.current = true;
    LPHub.track('form_start', { formId: hub.formId, firstField: key });
  };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (status === 'submitting') return; // chống bấm liên tiếp
    if (!e.currentTarget.checkValidity()) {
      e.currentTarget.reportValidity();
      return;
    }
    setStatus('submitting');
    setErrorDetail('');
    const data: Record<string, string> = {};
    for (const [k, v] of Object.entries(values)) if (!CUSTOMER_KEYS.includes(k)) data[k] = v;
    let res;
    if (form.type === 'order' && form.product) {
      const total = form.product.unitPrice * quantity;
      res = await session.current.submitOrder({
        customer: { name: values.name ?? '', phone: values.phone ?? '', email: values.email, address: values.address, note: values.note },
        items: [{ id: form.product.id, name: form.product.name, quantity, price: form.product.unitPrice }],
        subtotal: total,
        total,
        currency: form.product.currency,
        paymentMethod: 'cod',
        data,
      });
    } else if (form.type === 'custom') {
      res = await session.current.submitCustomForm({ data: { ...values } });
    } else {
      res = await session.current.submitLead({ name: values.name, phone: values.phone, email: values.email, data });
    }
    if (res.success) {
      setStatus('success');
      session.current.reset();
      session.current = LPHub.createSubmission(hub.formId);
    } else {
      setStatus('error');
      setErrorDetail(res.error?.message ?? res.message ?? '');
    }
  };

  return (
    <section id={form.id} ref={sectionRef} className="below-fold py-16 sm:py-20 bg-brand-surface">
      <div className="max-w-xl mx-auto px-4 sm:px-6">
        <div className="rounded-brand border border-brand-border bg-brand-background p-6 sm:p-10">
          {status === 'success' ? (
            <div role="status" className="text-center space-y-3">
              <h2 className="font-heading text-2xl font-bold text-brand-text"><Text value={form.successTitle} /></h2>
              <p className="text-brand-muted"><Text value={form.successMessage} /></p>
            </div>
          ) : (
            <form noValidate={false} onSubmit={onSubmit} className="space-y-5">
              <div>
                {form.eyebrow && (
                  <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-accent mb-2"><Text value={form.eyebrow} /></p>
                )}
                <h2 className="font-heading text-3xl font-bold text-brand-text"><Text value={form.title} /></h2>
                {form.intro && <p className="mt-2 text-brand-muted"><Text value={form.intro} /></p>}
              </div>
              {form.type === 'order' && form.product && (
                <div className="flex items-center justify-between gap-4 rounded-brand bg-brand-surface p-4">
                  <span className="font-medium text-brand-text"><Text value={form.product.name} /></span>
                  <label className="flex items-center gap-2 text-sm text-brand-muted" htmlFor="f_quantity">
                    Số lượng
                    <input
                      id="f_quantity"
                      type="number"
                      min={1}
                      max={99}
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, Number(e.target.value) || 1))}
                      className="field-input !w-20"
                    />
                  </label>
                </div>
              )}
              {form.fields.map((f) => (
                <div key={f.key}>
                  <label htmlFor={`f_${f.key}`} className="block text-sm font-semibold text-brand-text mb-1.5">
                    <Text value={f.label} />
                    {f.required && <span aria-hidden className="text-brand-accent"> *</span>}
                  </label>
                  <FieldControl f={f} value={values[f.key] ?? ''} onFocus={() => onFocus(f.key)} onChange={(v) => setValues((s) => ({ ...s, [f.key]: v }))} />
                  <p id={`e_${f.key}`} className="field-error">Vui lòng nhập đúng {f.label.toLowerCase()}.</p>
                </div>
              ))}
              {form.type === 'order' && form.product && (
                <p className="text-right font-semibold text-brand-text">
                  Tổng: {(form.product.unitPrice * quantity).toLocaleString('vi-VN')} {form.product.currency === 'VND' ? '₫' : form.product.currency}
                </p>
              )}
              {status === 'error' && (
                <div role="alert" className="rounded-brand border border-[#B91C1C] p-3 text-sm text-[#B91C1C]">
                  <Text value={form.errorMessage} /> {errorDetail && <span className="block opacity-80">({errorDetail})</span>}
                </div>
              )}
              <button
                type="submit"
                disabled={status === 'submitting'}
                aria-busy={status === 'submitting'}
                className="w-full min-h-[52px] rounded-brand bg-brand-primary text-brand-on-primary font-semibold text-lg hover:opacity-90 disabled:opacity-60 disabled:cursor-wait transition"
              >
                {status === 'submitting' ? 'Đang gửi…' : status === 'error' ? 'Thử gửi lại' : <Text value={form.submitLabel} />}
              </button>
              {form.consentText && <p className="text-xs text-brand-muted"><Text value={form.consentText} /></p>}
            </form>
          )}
        </div>
      </div>
    </section>
  );
};
