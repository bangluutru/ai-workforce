import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Bản production BẮT BUỘC có VITE_LPHUB_URL là https và không trỏ về máy local.
// Bản kiểm thử nội bộ: `npm run build:qa` (đọc .env.qa, cho phép http://localhost).
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const hubUrl = env.VITE_LPHUB_URL || '';
  if (command === 'build' && mode === 'production') {
    const isLocal = /localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]/i.test(hubUrl);
    if (!/^https:\/\//i.test(hubUrl) || isLocal) {
      throw new Error(
        `[LPHub] VITE_LPHUB_URL="${hubUrl}" không hợp lệ cho bản production. ` +
          'Khai báo URL https của Landing Hub trong .env.production (xem .env.production.example), ' +
          'hoặc dùng `npm run build:qa` cho bản kiểm thử nội bộ.'
      );
    }
  }
  return {
    plugins: [react()],
    server: { port: 3000 },
  };
});
