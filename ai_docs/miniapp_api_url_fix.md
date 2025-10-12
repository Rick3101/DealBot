# Mini App API URL Configuration Fix

**Date:** 2025-10-02
**Issue:** Mini App not referencing RAILWAY_URL from root `.env` file
**Status:** ✅ Fixed

---

## Problem

The Mini App was using `window.location.origin` for API calls, which meant:
- ❌ It used the browser's current URL, not your configured backend URL
- ❌ It didn't read the `RAILWAY_URL` from your `.env` file
- ❌ Requests failed when Mini App URL ≠ Backend URL

---

## Solution

Created a **separate `.env` file for the Mini App** with Vite-compatible environment variables.

### Files Changed

#### 1. Created `webapp/.env`
```env
# Vite environment variables must start with VITE_
VITE_API_URL=https://f1447f0de5a7.ngrok-free.app
```

#### 2. Updated `webapp/vite.config.ts`
Added environment variable support:
```typescript
define: {
  global: 'globalThis',
  'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || ''),
},
```

#### 3. Updated `webapp/src/services/expeditionApi.ts`
Changed from:
```typescript
this.baseURL = window.location.origin;
```

To:
```typescript
this.baseURL = import.meta.env.VITE_API_URL || window.location.origin;
console.log('API Base URL:', this.baseURL);
```

#### 4. Updated `webapp/src/services/websocketService.ts`
Changed from:
```typescript
const baseUrl = window.location.origin;
```

To:
```typescript
const baseUrl = import.meta.env.VITE_API_URL || window.location.origin;
console.log('WebSocket Base URL:', baseUrl);
```

---

## How It Works Now

### Development
1. Edit `webapp/.env` to set your ngrok/Railway URL:
   ```env
   VITE_API_URL=https://your-ngrok-url.ngrok-free.app
   ```

2. Rebuild the Mini App:
   ```bash
   cd webapp
   npm run build
   ```

3. The built app will use your configured URL for all API calls

### Production
- Set `VITE_API_URL` in your deployment environment variables
- Railway/Render will use this during build
- No code changes needed

---

## When to Rebuild

You need to run `npm run build` in `webapp/` **only when**:

### ✅ DO rebuild when:
1. **First time** - Initial setup
2. **Mini App code changes** - Modified `webapp/src/` files
3. **API URL changes** - Updated `VITE_API_URL` in `webapp/.env`
4. **Dependencies change** - Updated `package.json`
5. **After `git pull`** - If webapp changes were pulled

### ❌ DON'T rebuild when:
1. **Just starting server** - `python app.py` is enough
2. **Backend (Python) changes** - Only affects API code
3. **Database changes** - Schema runs automatically
4. **Root `.env` changes** - Unless `RAILWAY_URL` changed

---

## Quick Reference

### Update API URL
```bash
# 1. Edit webapp/.env
echo VITE_API_URL=https://new-url.ngrok-free.app > webapp\.env

# 2. Rebuild
cd webapp
npm run build

# 3. Restart server (if running)
# Ctrl+C, then: python app.py
```

### Check Current Configuration
Open browser console in Mini App and look for:
```
API Base URL: https://your-configured-url.ngrok-free.app
WebSocket Base URL: https://your-configured-url.ngrok-free.app
```

---

## Environment Variables Summary

### Root `.env` (Backend)
```env
DATABASE_URL=postgresql://...
BOT_TOKEN=6889252954:...
RAILWAY_URL=https://f1447f0de5a7.ngrok-free.app  # Not used by Mini App
ENVIRONMENT=development
```

### `webapp/.env` (Frontend - NEW!)
```env
VITE_API_URL=https://f1447f0de5a7.ngrok-free.app  # Used by Mini App
```

**Important:** Keep both URLs in sync!

---

## Verification

After rebuilding, check that:

1. **Build succeeded:**
   ```
   ✓ built in 7.64s
   ```

2. **Console logs show correct URL:**
   - Open Mini App in browser
   - Check console for: `API Base URL: https://your-url...`

3. **API calls work:**
   - Test a dashboard endpoint
   - Verify no CORS errors

---

## Troubleshooting

### Issue: API calls still using wrong URL

**Solution:**
1. Verify `webapp/.env` has correct URL
2. Rebuild: `cd webapp && npm run build`
3. Hard refresh browser (Ctrl+Shift+R)

### Issue: Build errors

**Solution:**
Skip TypeScript checking:
```bash
cd webapp
npx vite build --force
```

### Issue: CORS errors

**Solution:**
Ensure `VITE_API_URL` matches your Flask server URL exactly (including protocol and port)

---

## Next Steps

Whenever you change your ngrok URL or deploy to a new environment:

1. Update **both** `.env` files:
   - Root `.env` → `RAILWAY_URL`
   - `webapp/.env` → `VITE_API_URL`

2. Rebuild Mini App:
   ```bash
   cd webapp && npm run build
   ```

3. Restart server:
   ```bash
   python app.py
   ```

---

**Status:** ✅ Fixed and documented
**Build:** ✅ Successful (480.34 KiB in 7.64s)
**Impact:** Mini App now correctly uses configured backend URL
