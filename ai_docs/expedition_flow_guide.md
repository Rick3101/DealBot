# 🏴‍☠️ Expedition System - Complete User Guide

## Overview
The Expedition System is a comprehensive group buying and inventory management feature that allows users to create collaborative purchasing expeditions with progress tracking, anonymization, and financial management.

## Main Menu Access
- **Command**: `/expedition`
- **Permission Required**: Admin level or higher
- **Main Options**:
  - 🏴‍☠️ **Nova Expedição** - Create a new expedition
  - 📋 **Minhas Expedições** - View your expeditions
  - 📊 **Status da Expedição** - Check expedition progress
  - ❌ **Cancelar** - Cancel operation

---

## 1. Creating a New Expedition

### Step-by-Step Process

#### 1.1 Initial Setup
1. Use `/expedition` command
2. Click "🏴‍☠️ Nova Expedição"
3. **Enter Expedition Name**
   - Minimum: 3 characters
   - Maximum: 200 characters
   - Auto-sanitized for security

#### 1.2 Set Deadline
1. **Enter deadline in days** (1-30 days)
2. System calculates future deadline date
3. Deadline is used for progress monitoring

#### 1.3 Automatic Setup
- **Expedition Created** with unique ID
- **Owner Key Generated** for secure access
- **Pirate Name Assigned** for anonymization
- **Initial Status**: "Active"

### Example Flow
```
/expedition → Nova Expedição
Enter name: "GPU Group Buy 2024"
Enter deadline: 15
✅ Expedition Created!
🏴‍☠️ Nome: GPU Group Buy 2024
⏰ Prazo: 11/10/2024
🦜 Seu nome pirata: Captain Stormy
```

---

## 2. Expedition Management Features

### 2.1 View Your Expeditions (📋 Minhas Expedições)

#### Display Information
- **Expedition Status**: Active/Completed/Cancelled
- **Time Remaining**: Days until deadline
- **Progress Indicators**: Visual status emojis
- **Quick Actions**: Click expedition to view details

#### Status Indicators
- 📋 **Planning**: Initial setup phase
- 🏴‍☠️ **Active**: Currently running
- ✅ **Completed**: All items fulfilled
- 💀 **Failed**: Deadline missed
- ❌ **Cancelled**: Manually cancelled

### 2.2 Expedition Status (📊 Status da Expedição)

#### Detailed Progress View
- **Completion Percentage**: Overall progress
- **Item Progress**: Individual item fulfillment
- **Financial Summary**: Total spent/paid/unpaid
- **Timeline**: Key events and milestones
- **Participant Count**: Number of contributors

#### Financial Tracking
- **Total Consumption Value**: All purchases made
- **Paid Amount**: Confirmed payments
- **Outstanding Debt**: Pending payments
- **Payment Completion %**: Payment progress

---

## 3. Core System Features

### 3.1 Anonymization System
- **Pirate Names**: Automatically generated for privacy
- **Encrypted Mapping**: Secure name-to-user relationship
- **Owner Access**: Only expedition owner can decrypt real names
- **Privacy Protection**: No real names visible to participants

### 3.2 Progress Tracking
- **Item-Level Tracking**: Each product requirement monitored
- **Consumption Recording**: Real-time purchase tracking
- **Deadline Monitoring**: Automatic alerts for approaching deadlines
- **Completion Detection**: Automatic status updates

### 3.3 Integration with Sales System
- **FIFO Stock Consumption**: Automatic inventory management
- **Debt Tracking**: Integrated with payment system
- **Sale Records**: All purchases create sale entries
- **Payment Linking**: Connects expedition purchases to payments

---

## 4. Advanced Features

### 4.1 Expedition Analytics
Available through the expedition service:

#### Progress Metrics
- **Item Completion Percentage**: How many items are fully satisfied
- **Quantity Completion Percentage**: Total quantity progress
- **Payment Completion Percentage**: Financial completion status
- **Participant Analytics**: Unique contributors and activity

#### Timeline Tracking
- **Creation Events**: When expedition was started
- **Item Addition**: When requirements were added
- **Consumption Events**: Each purchase with timestamps
- **Completion Events**: When expedition finished

### 4.2 Export Capabilities
- **CSV Export**: Expedition data for external analysis
- **Progress Reports**: Detailed consumption and payment reports
- **Timeline Export**: Chronological event listing
- **Financial Summaries**: Profit/loss and payment status

### 4.3 Alert System
- **Deadline Alerts**: Notifications for approaching deadlines
- **Completion Notifications**: When items are fulfilled
- **Payment Reminders**: For outstanding debts
- **Status Changes**: Expedition lifecycle updates

---

## 5. Permission Levels & Access

### 5.1 Admin Level Access
- **Create Expeditions**: Start new group buying initiatives
- **View Own Expeditions**: See expeditions they created
- **Participate**: Contribute to any expedition
- **Track Progress**: Monitor expedition status

### 5.2 Owner Level Access (Additional)
- **View All Expeditions**: Access to all system expeditions
- **Decrypt Names**: Reveal real names behind pirate aliases
- **Manage Any Expedition**: Administrative control
- **Full Analytics**: Complete system-wide expedition analytics

---

## 6. Error Handling & Recovery

### 6.1 Common Scenarios
- **Invalid Names**: Automatic sanitization and validation
- **Deadline Issues**: Validation for reasonable timeframes
- **Database Errors**: Graceful degradation and retry logic
- **Service Failures**: Fallback mechanisms

### 6.2 Auto-Recovery Features
- **Database Auto-Init**: Automatically initializes missing components
- **Schema Migration**: Updates database structure as needed
- **Service Resilience**: Continues operation during partial failures

---

## 7. Technical Architecture

### 7.1 Data Flow
```
User Input → Handler → Service Layer → Database
                ↓
            Validation → Sanitization → Storage
                ↓
         Progress Tracking → Analytics → Reporting
```

### 7.2 Database Structure
- **expeditions**: Main expedition records
- **expedition_items**: Required items and quantities
- **item_consumptions**: Purchase tracking
- **pirate_names**: Anonymization mapping

### 7.3 Service Integration
- **Expedition Service**: Core expedition management
- **Brambler Service**: Pirate name generation and encryption
- **Sales Service**: Purchase and inventory integration
- **Analytics Service**: Progress and performance tracking

---

## 8. Best Practices

### 8.1 For Expedition Creators
- **Clear Names**: Use descriptive expedition names
- **Realistic Deadlines**: Allow sufficient time for completion
- **Monitor Progress**: Regular status checks
- **Participant Communication**: Keep contributors informed

### 8.2 For Participants
- **Prompt Participation**: Contribute early to avoid deadline pressure
- **Payment Responsibility**: Complete payments promptly
- **Status Awareness**: Check expedition progress regularly

### 8.3 For System Administrators
- **Regular Monitoring**: Watch for overdue expeditions
- **Performance Tracking**: Monitor system analytics
- **Data Backup**: Ensure expedition data preservation
- **User Support**: Assist with expedition management

---

## 9. Troubleshooting

### 9.1 Common Issues
- **Permission Denied**: Check user access level
- **Creation Failures**: Verify database connectivity
- **Missing Data**: Ensure schema is up to date
- **Progress Errors**: Check service synchronization

### 9.2 Recovery Steps
1. **Restart Services**: Basic recovery mechanism
2. **Database Check**: Verify schema and connectivity
3. **Cache Clear**: Reset any cached data
4. **Manual Intervention**: Contact system administrator

---

## 10. Future Enhancements

### 10.1 Planned Features
- **Multi-Item Expeditions**: Support for complex item lists
- **Advanced Analytics**: Deeper insights and reporting
- **Mobile Integration**: Enhanced mobile experience
- **API Access**: External system integration

### 10.2 Integration Opportunities
- **Notification System**: Real-time updates
- **Calendar Integration**: Deadline management
- **Payment Gateways**: Automated payment processing
- **Inventory Management**: Advanced stock control

---

This expedition system provides a comprehensive group buying solution with privacy protection, progress tracking, and seamless integration with your existing e-commerce bot infrastructure.