# Telegram Cloud Storage - Technical Overview

## What is Telegram Cloud Storage?

Telegram Cloud Storage is a **key-value storage API** provided by the Telegram Mini Apps platform that allows web applications running inside Telegram to store user-specific data on Telegram's servers.

## How It Works

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│ Your Mini App (webapp)                                  │
│ ┌─────────────────────────────────────────────────┐    │
│ │ JavaScript Code                                  │    │
│ │   window.Telegram.WebApp.CloudStorage.setItem() │────┼──┐
│ └─────────────────────────────────────────────────┘    │  │
└─────────────────────────────────────────────────────────┘  │
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Telegram Client (Mobile/Desktop/Web)                            │
│ - Handles encryption                                            │
│ - Manages authentication                                        │
│ - Sends encrypted data to Telegram servers                     │
└─────────────────────────────────────────────────────────────────┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Telegram Cloud (Telegram's Servers)                             │
│ - Stores encrypted data per user                                │
│ - Syncs across all user's devices                               │
│ - Persists indefinitely                                         │
└─────────────────────────────────────────────────────────────────┘
```

## API Methods

### 1. Set Item
```javascript
window.Telegram.WebApp.CloudStorage.setItem(key, value, callback)
```
- **key**: String identifier (your key name)
- **value**: String value to store
- **callback**: `(error, stored) => void`
  - `error`: Error message if failed, null if success
  - `stored`: Boolean indicating success

**Example**:
```javascript
Telegram.WebApp.CloudStorage.setItem('user_master_key', 'abc123...', (error, stored) => {
  if (error) {
    console.error('Failed to save:', error);
  } else {
    console.log('Saved successfully!');
  }
});
```

### 2. Get Item
```javascript
window.Telegram.WebApp.CloudStorage.getItem(key, callback)
```
- **key**: String identifier
- **callback**: `(error, value) => void`
  - `error`: Error message if failed, null if success
  - `value`: The stored value (string) or null if not found

**Example**:
```javascript
Telegram.WebApp.CloudStorage.getItem('user_master_key', (error, value) => {
  if (error) {
    console.error('Failed to load:', error);
  } else {
    console.log('Loaded:', value);
  }
});
```

### 3. Get Items (Multiple)
```javascript
window.Telegram.WebApp.CloudStorage.getItems(keys, callback)
```
- **keys**: Array of string identifiers
- **callback**: `(error, values) => void`

### 4. Remove Item
```javascript
window.Telegram.WebApp.CloudStorage.removeItem(key, callback)
```
- **key**: String identifier
- **callback**: `(error, removed) => void`

### 5. Remove Items (Multiple)
```javascript
window.Telegram.WebApp.CloudStorage.removeItems(keys, callback)
```

### 6. Get Keys
```javascript
window.Telegram.WebApp.CloudStorage.getKeys(callback)
```
- Returns all stored keys for this bot/user combination

## Technical Specifications

### Storage Limits
- **Per key**: Up to **4096 bytes** (4 KB)
- **Total keys**: Up to **1024 keys** per bot per user
- **Total storage**: ~4 MB per user per bot

### Data Scope
- **User-specific**: Each user has their own isolated storage
- **Bot-specific**: Data is tied to your bot (won't conflict with other bots)
- **Not shared**: One user cannot access another user's data

### Persistence
- **Permanent**: Data persists indefinitely (unless manually deleted)
- **Survives**: App reinstalls, cache clearing, device changes
- **Synced**: Automatically synced across all user's devices

### Security Features

1. **Encryption in Transit**
   - Data is encrypted when sent from client to Telegram servers
   - Uses Telegram's MTProto protocol encryption
   - HTTPS/TLS for Web version

2. **Access Control**
   - Only the specific user can access their data
   - Only within your specific bot context
   - No cross-bot or cross-user access

3. **Authentication**
   - Telegram handles all authentication
   - Uses Telegram's user session
   - No separate login required

4. **Server-Side Security**
   - Stored on Telegram's secure infrastructure
   - Managed by Telegram (you don't manage servers)
   - Subject to Telegram's security practices

## Comparison with Other Storage Options

| Feature | Cloud Storage | localStorage | sessionStorage | Cookies |
|---------|--------------|--------------|----------------|---------|
| **Persistence** | Permanent | Until cleared | Until tab closes | Until expiration |
| **Cross-device sync** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Storage size** | ~4 MB | 5-10 MB | 5-10 MB | 4 KB |
| **Encryption** | ✅ Yes (Telegram) | ❌ No | ❌ No | ❌ No |
| **Survives cache clear** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Requires internet** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Platform** | Telegram only | Any browser | Any browser | Any browser |

## Use Cases for Cloud Storage

### ✅ Good Use Cases
1. **User preferences** (theme, language, settings)
2. **Authentication tokens** (with caution)
3. **Encryption keys** (like your Master Key)
4. **User progress/state** (game progress, form data)
5. **Favorites/bookmarks**
6. **User-specific configuration**

### ❌ Not Recommended For
1. **Large files** (images, videos) - use Telegram's file storage
2. **Temporary data** - use sessionStorage
3. **Sensitive passwords** - avoid storing if possible
4. **Public data** - use your backend
5. **Real-time data** - use your backend with WebSocket

## Implementation in Your Project

### Current Implementation (masterKeyStorage.ts)

```typescript
// Save to Cloud Storage
public async setCloudStorage(key: string, value: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (!this.webApp?.CloudStorage) {
      // Fallback to localStorage
      localStorage.setItem(key, value);
      resolve(true);
      return;
    }

    this.webApp.CloudStorage.setItem(key, value, (error, stored) => {
      if (error) {
        console.error('Cloud storage error:', error);
        resolve(false);
      } else {
        resolve(stored || false);
      }
    });
  });
}

// Load from Cloud Storage
public async getCloudStorage(key: string): Promise<string | null> {
  return new Promise((resolve) => {
    if (!this.webApp?.CloudStorage) {
      // Fallback to localStorage
      resolve(localStorage.getItem(key));
      return;
    }

    this.webApp.CloudStorage.getItem(key, (error, value) => {
      if (error) {
        console.error('Cloud storage error:', error);
        resolve(null);
      } else {
        resolve(value || null);
      }
    });
  });
}
```

### Why It's Perfect for Master Keys

1. **Sync Across Devices**
   - User logs in on phone → saves key
   - Opens on desktop → key is already there
   - No manual export/import needed

2. **Survives Cache Clearing**
   - Browser cache cleared → localStorage lost
   - Cloud Storage → still available

3. **Telegram-Managed Security**
   - You don't manage encryption
   - You don't manage servers
   - Telegram handles security updates

4. **User Ownership**
   - Data belongs to user's Telegram account
   - User can clear from Telegram settings
   - Not stored on your backend

## Security Considerations

### What Telegram Cloud Storage Provides
- ✅ Encryption in transit (MTProto)
- ✅ User authentication (Telegram session)
- ✅ Access control (user/bot isolation)
- ✅ Infrastructure security (Telegram's servers)

### What It Does NOT Provide
- ❌ End-to-end encryption at rest
- ❌ Zero-knowledge architecture
- ❌ Client-side encryption (you can add this)
- ❌ Audit logs

### Additional Security You Can Add

```typescript
// Example: Client-side encryption before storing
import CryptoJS from 'crypto-js';

async function saveEncryptedKey(masterKey: string, userPassphrase: string) {
  // Encrypt before storing
  const encrypted = CryptoJS.AES.encrypt(masterKey, userPassphrase).toString();

  await Telegram.WebApp.CloudStorage.setItem('encrypted_key', encrypted);
}

async function loadEncryptedKey(userPassphrase: string) {
  const encrypted = await Telegram.WebApp.CloudStorage.getItem('encrypted_key');

  // Decrypt after loading
  const decrypted = CryptoJS.AES.decrypt(encrypted, userPassphrase).toString(CryptoJS.enc.Utf8);

  return decrypted;
}
```

## Availability

### When Cloud Storage is Available
- ✅ Telegram Desktop (all versions)
- ✅ Telegram Mobile (iOS/Android)
- ✅ Telegram Web (web.telegram.org)
- ✅ Telegram Web K (webk.telegram.org)

### When It's NOT Available
- ❌ Outside Telegram (regular browser)
- ❌ Development mode (unless mocked)
- ❌ Very old Telegram clients (< v6.0)

### Checking Availability

```typescript
if (window.Telegram?.WebApp?.CloudStorage) {
  console.log('Cloud Storage available!');
} else {
  console.log('Falling back to localStorage');
}
```

## Debugging Cloud Storage

### View Stored Data
1. **Desktop Telegram**:
   - Settings → Advanced → Manage data
   - Find your bot → View storage

2. **Mobile Telegram**:
   - Settings → Data and Storage → Storage Usage
   - Find your bot

3. **Programmatically**:
```javascript
Telegram.WebApp.CloudStorage.getKeys((error, keys) => {
  console.log('Stored keys:', keys);

  keys.forEach(key => {
    Telegram.WebApp.CloudStorage.getItem(key, (err, value) => {
      console.log(`${key}: ${value}`);
    });
  });
});
```

### Clear All Data
```javascript
Telegram.WebApp.CloudStorage.getKeys((error, keys) => {
  Telegram.WebApp.CloudStorage.removeItems(keys, (err, removed) => {
    console.log('Cleared all data');
  });
});
```

## Best Practices

### 1. Always Provide Fallback
```typescript
// Good: Fallback to localStorage
if (!CloudStorage) {
  localStorage.setItem(key, value);
}

// Bad: Assuming Cloud Storage always exists
CloudStorage.setItem(key, value); // May fail!
```

### 2. Handle Errors Gracefully
```typescript
CloudStorage.setItem(key, value, (error, stored) => {
  if (error) {
    // Fallback or user notification
    console.error('Save failed, using localStorage');
    localStorage.setItem(key, value);
  }
});
```

### 3. Don't Store Sensitive Data Unencrypted
```typescript
// Bad: Plain text password
CloudStorage.setItem('password', '12345');

// Good: Encrypted or hashed
const hashedPassword = await bcrypt.hash('12345', 10);
CloudStorage.setItem('password_hash', hashedPassword);
```

### 4. Validate Retrieved Data
```typescript
CloudStorage.getItem('user_settings', (error, value) => {
  if (value) {
    try {
      const settings = JSON.parse(value);
      // Validate schema
      if (settings.version !== CURRENT_VERSION) {
        // Migrate or reset
      }
    } catch (e) {
      // Handle corrupted data
      console.error('Invalid data, resetting');
    }
  }
});
```

## Documentation & Resources

- **Official Docs**: https://core.telegram.org/bots/webapps#cloudstorage
- **TypeScript Types**: Available in `@twa-dev/types`
- **Telegram Bot API**: https://core.telegram.org/bots/api

## Conclusion

Telegram Cloud Storage is a powerful, user-friendly storage solution specifically designed for Telegram Mini Apps. For your Master Key persistence use case, it's the **ideal choice** because:

1. ✅ Syncs across devices (user convenience)
2. ✅ Telegram-managed security (less risk for you)
3. ✅ Persists indefinitely (reliability)
4. ✅ User owns the data (privacy)
5. ✅ Simple API (easy to implement)

Your implementation with localStorage as fallback ensures maximum compatibility and reliability!
