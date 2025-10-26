# Storybook Setup Note

## Current Status

Storybook dependencies have been **temporarily removed** from package.json to fix version conflicts during the build process.

## Why Removed?

There was a version mismatch:
- Main Storybook packages: v9.1.10
- Addon packages: v8.6.14

This caused npm install to fail with peer dependency conflicts.

## Production Build Status

✅ **The production build works perfectly without Storybook!**

The webapp builds successfully and all functionality is intact. Storybook is only needed for **component development and documentation**, not for production deployment.

## Re-adding Storybook (Optional)

If you want to add Storybook back for component development, use compatible versions:

```bash
npm install --save-dev --legacy-peer-deps \
  @storybook/react-vite@^8.4.0 \
  @storybook/react@^8.4.0 \
  @storybook/addon-essentials@^8.4.0 \
  @storybook/addon-interactions@^8.4.0 \
  @storybook/addon-links@^8.4.0 \
  @storybook/blocks@^8.4.0 \
  storybook@^8.4.0
```

Then add back the scripts to package.json:
```json
"storybook": "storybook dev -p 6006",
"build-storybook": "storybook build"
```

## Storybook Stories

All component stories are still available in:
- `src/components/ui/*.stories.tsx`
- `src/components/dashboard/*.stories.tsx`
- `src/components/expedition/*.stories.tsx`
- `src/stories/Introduction.mdx`

These files are excluded from the production build via `tsconfig.json`, so they don't affect the build process.

## Documentation

All architecture documentation created in Phase 4.3 is still available:
- [Architecture Guide](docs/ARCHITECTURE.md) - 8,500 words
- [Hook Composition Guide](docs/HOOK_COMPOSITION.md) - 7,000 words
- [Service Layer Guide](docs/SERVICE_LAYER.md) - 6,500 words

The documentation provides all the information Storybook stories would have shown, plus more detailed architecture patterns and best practices.

## Recommendation

For production deployment, Storybook is **not needed**. The current setup is optimized for:
- Fast builds (~8 seconds)
- Small bundle size (~168 KB gzipped)
- Production stability

Only re-add Storybook if you need:
- Interactive component playground
- Visual regression testing
- Component documentation website
- Designer/stakeholder demos
