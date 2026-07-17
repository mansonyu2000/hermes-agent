import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'

// `hgui` symlinks a worktree's node_modules to the main checkout. Vite realpaths
// those before enforcing server.fs.allow, so codicon/font assets resolve outside
// the worktree root and 404. Whitelist the real node_modules locations.
const real = (p: string): string | null => {
  try {
    return fs.realpathSync(p)
  } catch {
    return null
  }
}

const fsAllow = [
  ...new Set(
    [
      path.resolve(__dirname, '../..'),
      real(path.resolve(__dirname, 'node_modules')),
      real(path.resolve(__dirname, '../../node_modules'))
    ].filter((p): p is string => p !== null)
  )
]

// ── Patch leva imports for zustand v5 ──────────────────────────
// leva@0.10.1 uses `import create from 'zustand'` (CJS default export).
// zustand@5.x removed the default export (ESM named exports only).
// This plugin rewrites leva's imports to use named exports at build time,
// without touching npm resolution — works in dev and production builds.
const fixLevaZustandPlugin = () => ({
  name: 'fix-leva-zustand',
  transform(code: string, id: string) {
    if (!id.includes('leva')) return
    // Vite dev adds ?v=... query suffix — strip before extension check
if (!/\.(m?js)(\?|$)/.test(id)) return
    return {
      code: code
        .replace(
          /import\s+create\s+from\s+['"]zustand['"]/,
          'import { create } from \'zustand\'',
        )
        .replace(
          /import\s+shallow\s+from\s+['"]zustand\/shallow['"]/,
          'import { shallow } from \'zustand/shallow\'',
        ),
      map: null,
    }
  },
})

export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss(), fixLevaZustandPlugin()],
  css: {
    // Pin an explicit (empty) PostCSS config. Tailwind is handled entirely by
    // `@tailwindcss/vite`, so the renderer needs no PostCSS plugins — and
    // without this, Vite's `postcss-load-config` walks UP the filesystem
    // looking for a stray `postcss.config.*` / `tailwind.config.*`. The desktop
    // build runs from inside the user's home tree (e.g.
    // `C:\Users\<name>\AppData\Local\hermes\hermes-agent\apps\desktop`), so an
    // unrelated Tailwind v3 config higher up the tree gets picked up and
    // reprocesses our v4 stylesheet, failing the build with
    // "`@layer base` is used but no matching `@tailwind base` directive is
    // present." Pinning the config makes the build hermetic.
    postcss: { plugins: [] }
  },
  build: {
    // Keep desktop packaging stable: Shiki ships many dynamic chunks by
    // default, and electron-builder can OOM scanning thousands of files.
    // Collapsing to a single chunk is intentional, so the renderer bundle is
    // large by design (~22 MB). Raise the warning ceiling above that so the
    // cosmetic "chunk larger than 500 kB" nag stays quiet, while still acting
    // as a regression alarm if the bundle balloons well past today's size.
    chunkSizeWarningLimit: 25000,
    rolldownOptions: {
      output: {
        codeSplitting: false
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@hermes/shared': path.resolve(__dirname, '../shared/src'),
      react: path.resolve(__dirname, '../../node_modules/react'),
      'react-dom': path.resolve(__dirname, '../../node_modules/react-dom'),
      'react/jsx-dev-runtime': path.resolve(__dirname, '../../node_modules/react/jsx-dev-runtime.js'),
      'react/jsx-runtime': path.resolve(__dirname, '../../node_modules/react/jsx-runtime.js')
    },
    dedupe: ['react', 'react-dom', 'zustand']
  },
  optimizeDeps: {
    // Only leva needs exclusion — its zustand imports must pass through
    // the transform plugin first. Other deps (attr-accept etc.) stay in
    // so esbuild wraps them with synthetic default exports.
    exclude: ['leva'],
  },
  server: {
    host: '127.0.0.1',
    port: Number(process.env.HERMES_DESKTOP_DEV_PORT) || 5175,
    strictPort: true,
    fs: {
      allow: fsAllow
    }
  },
  preview: {
    host: '127.0.0.1',
    port: 4174
  }
})
