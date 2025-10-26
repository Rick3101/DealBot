/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly DEV: boolean
  readonly PROD: boolean
  // add other env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}