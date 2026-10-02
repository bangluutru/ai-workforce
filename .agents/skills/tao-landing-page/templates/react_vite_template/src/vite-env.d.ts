/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_LPHUB_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
