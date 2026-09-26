import React, { useState } from 'react';

interface RegisterFormData {
  fullName: string;
  email: string;
}

export const HeroSection: React.FC = () => {
  const [formData, setFormData] = useState<RegisterFormData>({ fullName: '', email: '' });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.fullName.trim()) {
      setStatus('error');
      setErrorMessage('Vui lòng nhập họ và tên của bạn.');
      return;
    }
    if (!validateEmail(formData.email)) {
      setStatus('error');
      setErrorMessage('Địa chỉ email không hợp lệ.');
      return;
    }

    setStatus('loading');
    setErrorMessage('');

    try {
      // Giả lập tương thích gửi về Landing Hub API endpoint
      await new Promise((resolve) => setTimeout(resolve, 800));
      setStatus('success');
    } catch {
      setStatus('error');
      setErrorMessage('Không thể kết nối máy chủ. Vui lòng thử lại sau.');
    }
  };

  return (
    <section className="relative overflow-hidden bg-slate-950 py-20 px-6 sm:px-12 text-white">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 to-cyan-300 bg-clip-text text-transparent">
          Tự Động Hóa Doanh Nghiệp Với 16 Nhân Sự Số
        </h1>
        <p className="mt-6 text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto">
          Hệ thống tác nhân số vận hành trên Antigravity IDE - 100% Native, Zero Setup Hassle.
        </p>

        {status === 'success' ? (
          <div className="mt-10 p-6 bg-teal-900/40 border border-teal-500 rounded-xl text-teal-200">
            🎉 Đăng ký thành công! Vé mời tham dự webinar đã được gửi tới email của bạn.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-10 max-w-md mx-auto flex flex-col gap-4 text-left">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Họ và Tên</label>
              <input
                type="text"
                value={formData.fullName}
                onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                disabled={status === 'loading'}
                placeholder="Nguyễn Văn A"
                className="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-teal-400"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Email Công Việc</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                disabled={status === 'loading'}
                placeholder="name@company.com"
                className="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-teal-400"
              />
            </div>
            {status === 'error' && (
              <p className="text-red-400 text-sm">{errorMessage}</p>
            )}
            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full py-3.5 px-6 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold transition duration-200 disabled:opacity-50"
            >
              {status === 'loading' ? 'Đang Xử Lý...' : 'Nhận Vé Mời Miễn Phí'}
            </button>
          </form>
        )}
      </div>
    </section>
  );
};

export default HeroSection;
