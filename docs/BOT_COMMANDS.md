# 🤖 Complete Bot Commands List

## 🎯 **Universal Commands** (No Login Required)
- `/start` - Bot initialization with custom protection phrase
- `/login` - User authentication flow with auto-cleanup

## 👤 **User Level Commands** (After Login)
- `/commands` - Dynamic command listing based on your permission level

## 👮 **Admin Level Commands** (Includes User + Admin Commands)

### Core Operations
- `/buy` - Purchase flow with inventory validation and FIFO processing
  - **Owner:** Can specify buyer name
  - **Admin:** Auto-uses authenticated username  
  - **Secret Menu:** "secred words" unlocks hidden products (👹 emojis configured via .env)

- `/estoque` - Inventory management with batch operations
  - **Format:** `quantity / price / cost`
  - **Batch Operations:** Multiple product updates

- `/pagar` - Payment processing with debt tracking
  - **Debt Tracking:** Comprehensive payment history
  - **Partial Payments:** Flexible payment amounts

### Reports & Information
- `/lista_produtos` - Product catalog with media display
- `/relatorios` - Sales/debt reports with CSV export
  - **Sales Reports:** Complete transaction history
  - **Debt Reports:** By buyer with filtering  
  - **CSV Export:** Temporary file generation with auto-cleanup

- `/dividas` - Personal debt report with CSV export
  - **Auto-Authentication:** Shows only your own purchases/debts
  - **CSV Export:** Personal debt export as `minhas_dividas_{username}.csv`
  - **Auto-Cleanup:** Message auto-deletes after 30 seconds

## 👑 **Owner Level Commands** (Includes User + Admin + Owner Commands)

### User Management
- `/user` - Complete user management system
  - **Security:** Password validation, secure storage
  - **Role Management:** user, admin, owner levels
  - **Input Sanitization:** Comprehensive validation

### Product Management  
- `/product` - Product CRUD with media management
  - **Add Product:** Name → Emoji → Optional media (photo/video/document)
  - **Edit Product:** Select product → Choose property → Update with validation
  - **Media Management:** Protected files with ID preservation

### Smart Contracts
- `/smartcontract` - Smart contract creation and transaction management
  - **Creation:** `/smartcontract <code>` creates contract
  - **Management:** Multi-party transaction system
  - **Features:** Confirmation workflow, history tracking

### Additional Features
- `/transactions` - Transaction management menu

## 🛠️ **System/Utility Commands**
- `/cancel` - Cancel any current operation (works in all conversation flows)
- `/delete_my_data` - Delete your user data from the system
- `/unauthorized` - Handle unauthorized access scenarios  
- `/detalhes` - Detailed sales information

## 🔐 **Permission Levels Explained**

1. **👤 User:** Basic access, can view commands and login
2. **👮 Admin:** Business operations, purchases, payments, reports  
3. **👑 Owner:** Full system control, user management, product management, smart contracts

## 🎯 **Special Features**

### **Secret Menu** 🤫
- Type "secret words ( configured via .env )" during purchase flow to unlock hidden products ( emojis are what we use to filter it , its configured via .env too)

### **Auto-Features**
- **Auto-deletion:** Sensitive messages delete automatically
- **Auto-cleanup:** CSV files and temporary data cleaned up automatically  
- **Auto-authentication:** System remembers your login for streamlined operations

### **Advanced Operations**
- **FIFO Processing:** Inventory consumed on first-in-first-out basis
- **Media Support:** Products can have photos, videos, or documents
- **CSV Export:** All reports exportable to CSV format
- **Input Validation:** All inputs sanitized and validated for security

## 📋 **Detailed Command Flows**

### Login Flow (`/login`)
**States:** `LOGIN_USERNAME` → `LOGIN_PASSWORD`
- Input validation and sanitization
- Secure credential verification
- Chat ID association
- Auto-deletion of sensitive messages

### Product Management (`/product`) - Owner only
**States:** `PRODUCT_MENU` → `PRODUCT_ADD_NAME` → `PRODUCT_ADD_EMOJI` → `PRODUCT_ADD_MEDIA_CONFIRM` → `PRODUCT_ADD_MEDIA`
- **Add Product:** Name → Emoji → Optional media (photo/video/document)
- **Edit Product:** Select product → Choose property → Update with validation
- **Media Management:** Protected files with ID preservation

### Purchase Flow (`/buy`) - Admin+
**States:** `BUY_NAME` → `BUY_SELECT_PRODUCT` → `BUY_QUANTITY` → `BUY_PRICE`
- **Owner:** Can specify buyer name
- **Admin:** Auto-uses authenticated username
- **Secret Menu:** "wubba lubba dub dub" unlocks hidden products (🧪💀 emojis)
- **Inventory Validation:** Real-time stock checking
- **FIFO Processing:** Automatic stock consumption

### User Management (`/user`) - Owner only
**States:** `MENU` → `ADD_USERNAME`/`REMOVE_USER`/`EDIT_SELECT_USER` → `ADD_PASSWORD`/`EDIT_ACTION` → `EDIT_NEW_VALUE`/`EDIT_NIVEL`
- **Security:** Password validation, secure storage
- **Role Management:** user, admin, owner levels
- **Input Sanitization:** Comprehensive validation

### Inventory Management (`/estoque`)
**States:** `ESTOQUE_MENU` → `ESTOQUE_ADD_SELECT` → `ESTOQUE_ADD_VALUES`
- **Format:** `quantity / price / cost`
- **Batch Operations:** Multiple product updates
- **Validation:** Strict input format checking

### Smart Contracts (`/smartcontract`) - Owner only
**States:** `TRANSACTION_MENU` → `TRANSACTION_DESCRICAO`
- **Creation:** `/smartcontract <code>` creates contract
- **Management:** Multi-party transaction system
- **Features:** Confirmation workflow, history tracking

### Payment Processing (`/pagar`) - Admin+
**States:** `PAGAMENTO_VALOR`
- **Debt Tracking:** Comprehensive payment history
- **Partial Payments:** Flexible payment amounts
- **Auto-completion:** Automatic status updates

### Reports (`/relatorios`) - Admin+
**States:** `RELATORIO_MENU` → `RELATORIO_DIVIDA_NOME`
- **Sales Reports:** Complete transaction history
- **Debt Reports:** By buyer with filtering
- **CSV Export:** Temporary file generation with auto-cleanup

### Personal Debts (`/dividas`) - Admin+
**Direct Command:** No conversation states - immediate response
- **Auto-Authentication:** Uses authenticated user's chat_id to get username
- **Personal Report:** Shows only the user's own purchases/debts
- **Total Calculation:** Displays running total of all debts
- **CSV Export:** Personal debt export with filename `minhas_dividas_{username}.csv`
- **Auto-Cleanup:** Message auto-deletes after 30 seconds

## 🔧 **Advanced Features**

### **Message Management**
- Auto-deletion with configurable delays
- Protected message system for important content
- Conversation state management with locks

### **Security Features**
- Input sanitization and validation
- Rate limiting and flood protection
- Secure credential handling
- Permission-based access control

### **Data Processing**
- FIFO inventory consumption
- Complex debt calculations
- Media file preservation
- CSV generation with proper cleanup

---

**💡 Quick Tip:** Use `/commands` after logging in to see only the commands available to your permission level!

**🏗️ Architecture:** This bot uses a modern enterprise-grade architecture with dependency injection, service containers, and comprehensive configuration management for reliable e-commerce operations.