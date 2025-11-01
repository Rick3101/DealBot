# How to Check if Render Has the New Build

## The Situation

- ✅ **Local build**: Works perfectly, no PWA files, no errors
- ❌ **Render build**: Still showing old version with errors

## Quick Diagnostic Tests

### Test 1: Check if registerSW.js exists on Render

Visit this URL directly in your browser:
```
https://dealbot.onrender.com/webapp/registerSW.js
```

**Expected Results:**

**✅ NEW BUILD (PWA disabled)**:
- Should return **404 Not Found**
- File doesn't exist anymore

**❌ OLD BUILD (PWA still there)**:
- Returns **200 OK** with JavaScript code
- File still exists

### Test 2: Check index.html source

Visit:
```
https://dealbot.onrender.com/webapp
```

1. Right-click → "View Page Source"
2. Search for: `registerSW`

**Expected Results:**

**✅ NEW BUILD**:
- NO mention of "registerSW" in the HTML
- NO service worker script tags

**❌ OLD BUILD**:
- Has: `<script src="/webapp/registerSW.js"></script>`
- Service worker code present

### Test 3: Check Render Dashboard

1. Go to: https://dashboard.render.com
2. Open your service
3. Click "Events" tab
4. Look for latest deployment

**Check for:**
- Date/time of last deploy
- Commit hash: Should be `42109648`
- Status: Should be "Deploy live" (not "Building")

### Test 4: Check Build Logs

In Render dashboard → Logs tab:

Search for these lines (most recent):
```
Step 28/30 : RUN rm -rf dist
Step 29/30 : RUN npm install
Step 30/30 : RUN npm run build
```

Then look for:
```
vite v4.5.14 building for production...
✓ built in XXs
```

**Key thing to check:**
- Build output should NOT show: `dist/registerSW.js`
- Should only show: `dist/index.html` and `dist/assets/...`

## If Render Still Has Old Build

### Possible Reasons:

1. **Build is still running**
   - Wait for "Deploy live" in Events tab
   - Can take 10-15 minutes for full Docker build

2. **Build failed**
   - Check Logs for errors
   - Look for "Build failed" message

3. **Render is cached**
   - Try "Manual Deploy" → "Clear build cache & deploy"

4. **Docker layer caching**
   - The `rm -rf dist` should fix this
   - But may need to wait for next build

## Force New Deployment

If it's been > 15 minutes and still showing old build:

### Option 1: Manual Deploy with Cache Clear

1. Render dashboard → your service
2. Click "Manual Deploy" button (top right)
3. Select "Clear build cache & deploy"
4. Wait ~10 minutes

### Option 2: Make a Dummy Commit

```bash
# Add a comment to trigger rebuild
echo "# Force rebuild" >> webapp/README.md
git add webapp/README.md
git commit -m "Force rebuild - trigger new deployment"
git push
```

### Option 3: Check Dockerfile in Render

Make sure Render is using the latest Dockerfile with:
```dockerfile
RUN rm -rf dist  # This line should be there
```

## Timeline Check

When was the last push?

```bash
git log --oneline -1
```

Should show:
```
42109648 Disable PWA/service worker - fixes Request undefined error in Telegram Mini App
```

**When was it pushed?**
- Check timestamp with: `git log -1 --format=%cd`
- If > 15 minutes ago and Render still shows old build → something is wrong

## What's Happening

### Theory:

1. ✅ Code is correct (PWA disabled locally)
2. ✅ Code is pushed to GitHub
3. ❓ Render build status unknown
4. ❌ You're seeing old build

### Most Likely:

**Render is still building** OR **hasn't picked up the changes yet**.

### How to Confirm:

Run all 4 tests above. If they all show OLD build, then:
- Render hasn't deployed new version yet
- Need to wait or force rebuild

## Expected Timeline

```
T+0:   Push code (42109648)
T+1:   Render webhook triggers
T+2:   Docker build starts
T+5:   Installing dependencies
T+8:   Building webapp (npm run build)
T+12:  Creating Docker image
T+15:  Deploy complete ✅
```

**If T > 20 minutes:**
- Check Render dashboard for errors
- Check if auto-deploy is enabled
- May need to trigger manual deploy

## Debug Output

To help diagnose, check these:

### 1. Git Status
```bash
git log --oneline -3
```

Should show:
```
42109648 Disable PWA/service worker
97186f31 Force clean webapp build
a1eef738 Fix webapp asset 404 errors
```

### 2. Local Build Output
```bash
cd webapp
npm run build
ls dist/
```

Should show:
```
index.html
assets/
manifest.json
pirate-logo.svg
test-api.html

NO registerSW.js ✅
NO sw.js ✅
```

### 3. Render Status
Check dashboard for:
- Last deploy time
- Build status
- Any error messages

## Next Steps

1. **Run Test 1** (check registerSW.js URL)
2. **If 404** → New build is live! Clear browser cache and retry
3. **If 200** → Render hasn't deployed yet, wait or force rebuild

---

**Quick Test**: Visit https://dealbot.onrender.com/webapp/registerSW.js

- **404** = New build is live (good!)
- **200** = Old build still there (wait or force rebuild)
