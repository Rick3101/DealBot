# WebApp Deployment Workflow

## Quick Answer

**You DON'T need to run `npm run build` before committing!**

Render will automatically build the webapp during deployment. Just commit your source code changes.

## How It Works

### Current Setup (Automated Build on Render)

```
GitHub Push → Render Build → Deploy
     ↓            ↓           ↓
  Source      Build Webapp  Serve
   Code       on Server     App
```

### What Happens on Render:

When you push to GitHub, Render runs this build command:

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node dependencies and build webapp
cd webapp && npm install && npm run build
```

This creates the `webapp/dist/` folder on Render's servers automatically.

## Your Workflow for WebApp Updates

### Step 1: Make Changes to WebApp
Edit any files in the `webapp/src/` folder:
- React components
- TypeScript files
- Styles (CSS/Tailwind)
- Assets

### Step 2: Test Locally (Optional but Recommended)

```bash
# Navigate to webapp folder
cd webapp

# Install dependencies (first time only)
npm install

# Run development server
npm run dev

# Test in browser at http://localhost:5173
# Make sure everything works!
```

### Step 3: Commit ONLY Source Code

```bash
# Add only source files (NOT dist folder)
git add webapp/src/
git add webapp/package.json  # if you added dependencies
git add webapp/index.html    # if you changed it
# etc...

# Commit
git commit -m "Update WebApp: add new expedition feature"

# Push to GitHub
git push
```

**IMPORTANT:**
- ✅ DO commit: `webapp/src/`, `webapp/package.json`, `webapp/index.html`, etc.
- ❌ DON'T commit: `webapp/dist/`, `webapp/node_modules/`

### Step 4: Wait for Render to Deploy

1. Render detects the GitHub push
2. Render runs the build command
3. WebApp is built fresh on the server
4. App is deployed automatically

## Why This Approach?

### Advantages of Building on Server:

1. **Cleaner Git History**
   - Only source code is tracked
   - No huge binary files (built JS bundles)
   - Smaller repository size

2. **Consistency**
   - Same build environment every time
   - No "works on my machine" issues
   - Same Node.js version on server

3. **Simpler Workflow**
   - No manual build step
   - No risk of forgetting to build
   - Automatic on every deploy

4. **Better Collaboration**
   - Other developers don't need to deal with built files
   - No merge conflicts in dist files

## Current .gitignore Setup

Your `.gitignore` correctly excludes:

```gitignore
# Python build artifacts
dist/
build/

# This ignores webapp/dist/ folder ✅
```

This means `webapp/dist/` is NOT committed to git (which is correct).

## Complete Deployment Checklist

### For WebApp Changes:

- [ ] 1. Make changes in `webapp/src/`
- [ ] 2. Test locally with `npm run dev` (optional)
- [ ] 3. Commit source files only (no dist/)
- [ ] 4. Push to GitHub
- [ ] 5. Monitor Render logs for build success
- [ ] 6. Test deployed app at `https://your-app.onrender.com/webapp`

### For Python Backend Changes:

- [ ] 1. Make changes in Python files
- [ ] 2. Test locally (optional)
- [ ] 3. Commit changes
- [ ] 4. Push to GitHub
- [ ] 5. Render deploys automatically

### For Both WebApp + Backend:

- [ ] 1. Make changes in both areas
- [ ] 2. Test locally
- [ ] 3. Commit all source changes
- [ ] 4. Push to GitHub
- [ ] 5. Render builds both and deploys

## Build Configuration Details

### From render.yaml:

```yaml
buildCommand: |
  pip install -r requirements.txt
  cd webapp && npm install && npm run build
```

This runs on **every deployment** automatically.

### What `npm run build` Does:

From `webapp/package.json`:
```json
{
  "scripts": {
    "build": "vite build"
  }
}
```

- Compiles TypeScript to JavaScript
- Bundles all React components
- Optimizes and minifies code
- Copies assets to `dist/`
- Creates production-ready files

## Troubleshooting

### Issue: WebApp changes not showing up

**Causes:**
1. Browser cache
2. Build failed on Render
3. Changes not actually committed

**Solutions:**
```bash
# 1. Hard refresh browser
# Windows: Ctrl + Shift + R
# Mac: Cmd + Shift + R

# 2. Check Render logs
# Look for "npm run build" output
# Check for errors

# 3. Verify commit
git log -1 --stat
# Should show your webapp changes
```

### Issue: Build fails on Render

**Check Render logs for:**
```
npm ERR! code ELIFECYCLE
npm ERR! errno 1
```

**Common causes:**
- TypeScript errors
- Missing dependencies in package.json
- Syntax errors

**Fix:**
```bash
# Run build locally first to catch errors
cd webapp
npm run build

# Fix any errors shown
# Then commit and push
```

### Issue: Changes work locally but not on Render

**Possible causes:**
1. Environment variables different
2. API endpoints hardcoded to localhost
3. Missing dependencies

**Check:**
```typescript
// ❌ BAD - hardcoded localhost
const API_URL = "http://localhost:5000/api"

// ✅ GOOD - use environment or relative path
const API_URL = import.meta.env.VITE_API_URL || "/api"
```

## Advanced: Build Optimization

### Current Build Output:

After build, `webapp/dist/` contains:
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js      # Main JS bundle
│   ├── vendor-[hash].js     # Third-party libraries
│   ├── index-[hash].css     # Styles
│   └── ...
├── manifest.json
└── ...
```

### Build Performance:

- **Build time on Render:** ~1-3 minutes
- **Includes:** Dependencies install + build
- **Optimizations:** Minification, tree-shaking, code splitting

## Local Development vs Production

### Local Development:
```bash
cd webapp
npm run dev
# Fast hot-reload, source maps, no minification
# Access at http://localhost:5173
```

### Production Build (what Render does):
```bash
cd webapp
npm run build
# Optimized, minified, production-ready
# Output to dist/
```

### Viewing Production Build Locally:
```bash
cd webapp
npm run build        # Build production version
npm run preview      # Preview production build
# Access at http://localhost:4173
```

## Monitoring Deployments

### In Render Dashboard:

1. **Events Tab**
   - Shows all deployments
   - Build logs
   - Deploy status

2. **Logs Tab**
   - Runtime logs
   - Application output
   - Errors

### What to Watch For:

```
✅ Good Build Log:
==> Installing dependencies
==> $ pip install -r requirements.txt
==> $ cd webapp && npm install && npm run build
vite v5.x.x building for production...
✓ built in 45.32s
==> Build successful!

❌ Failed Build Log:
==> $ npm run build
ERROR: TypeScript error in src/...
==> Build failed
```

## Quick Reference Commands

### Local Development:
```bash
# Start dev server
cd webapp && npm run dev

# Build production version
cd webapp && npm run build

# Preview production build
cd webapp && npm run preview

# Type checking
cd webapp && npm run type-check

# Linting
cd webapp && npm run lint
```

### Git Workflow:
```bash
# Check what will be committed
git status

# Add webapp source changes
git add webapp/src/

# Commit
git commit -m "feat: add expedition analytics dashboard"

# Push and auto-deploy
git push
```

### Verify Deployment:
```bash
# Check health
curl https://your-app.onrender.com/health

# Test webapp loads
curl https://your-app.onrender.com/webapp

# Check specific API endpoint
curl https://your-app.onrender.com/api/expeditions
```

## Summary

### ✅ DO:
- Commit source code in `webapp/src/`
- Let Render build the webapp
- Test locally before pushing
- Check Render logs after deployment

### ❌ DON'T:
- Run `npm run build` before committing
- Commit `webapp/dist/` folder
- Commit `node_modules/`
- Push without testing locally first

### The Golden Rule:
**Commit source, let Render build!**

---

**Last Updated**: 2025-10-26
**Build System**: Vite
**Deployment**: Automatic on GitHub push
