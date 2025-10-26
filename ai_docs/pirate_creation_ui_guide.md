# Pirate Creation UI Guide

## Overview
This guide shows you where to find and how to use the new "Create Pirate" feature in the webapp.

## Location
**Page:** Brambler Maintenance
**URL:** `/brambler-maintenance` (accessible from main navigation)

## UI Components

### 1. Create Pirate Button
**Location:** Top right section of the page, next to the total pirates count

**Appearance:**
- Green button with text "Create Pirate"
- Plus icon (+) on the left
- Located in the controls section near "Show/Hide Original Names" button

**How to Access:**
1. Navigate to Brambler Maintenance from the main menu
2. Look at the top controls area
3. Find the green "+ Create Pirate" button on the right side

### 2. Create Pirate Modal
**Triggered by:** Clicking the "Create Pirate" button

**Modal Structure:**
```
┌─────────────────────────────────────┐
│  👥 Create New Pirate          [X]  │
├─────────────────────────────────────┤
│                                     │
│  Expedition *                       │
│  [Dropdown: Select expedition...]  │
│  Choose which expedition...         │
│                                     │
│  Original Name *                    │
│  [Input: Enter the real buyer...] │
│  The actual name of the buyer...   │
│                                     │
│  Pirate Name (Optional)            │
│  [Input: Leave empty for auto...] │
│  Leave blank to auto-generate...   │
│                                     │
│  [Cancel]  [Create Pirate]         │
└─────────────────────────────────────┘
```

### 3. Form Fields

#### Expedition Dropdown (Required)
- **Label:** "Expedition *"
- **Type:** Select/Dropdown
- **Options:** Lists all active expeditions by name
- **Help Text:** "Choose which expedition this pirate will join"
- **Validation:** Must be selected

#### Original Name Input (Required)
- **Label:** "Original Name *"
- **Type:** Text Input
- **Placeholder:** "Enter the real buyer/consumer name"
- **Help Text:** "The actual name of the buyer/consumer (required)"
- **Validation:** Cannot be empty

#### Pirate Name Input (Optional)
- **Label:** "Pirate Name (Optional)"
- **Type:** Text Input
- **Placeholder:** "Leave empty for auto-generated name"
- **Help Text:** "Leave blank to auto-generate, or enter a custom pirate name"
- **Behavior:** If left empty, system generates a pirate name automatically

### 4. Action Buttons

#### Cancel Button
- **Location:** Bottom left of modal
- **Style:** Secondary/outlined button
- **Action:** Closes modal without creating pirate

#### Create Pirate Button
- **Location:** Bottom right of modal
- **Style:** Primary button (blue/gold color)
- **Text:** "Create Pirate" (changes to "Creating..." during submission)
- **Action:** Submits form and creates new pirate

## Usage Examples

### Example 1: Create Pirate with Auto-Generated Name
1. Click "+ Create Pirate" button
2. Select "Ice Age" from expedition dropdown
3. Enter "John Doe" in Original Name field
4. Leave Pirate Name field empty
5. Click "Create Pirate"
6. **Result:** New pirate appears with name like "Capitão Coração de Pedra o Terrível"

### Example 2: Create Pirate with Custom Name
1. Click "+ Create Pirate" button
2. Select "Summer Expedition" from expedition dropdown
3. Enter "Jane Smith" in Original Name field
4. Enter "Almirante Jane das Sete Mares" in Pirate Name field
5. Click "Create Pirate"
6. **Result:** New pirate appears with exact name "Almirante Jane das Sete Mares"

## Error Messages

### Missing Expedition
**Error:** "Please select an expedition"
**Trigger:** Clicking Create without selecting expedition
**Solution:** Select an expedition from the dropdown

### Missing Original Name
**Error:** "Original name is required"
**Trigger:** Clicking Create without entering original name
**Solution:** Enter a name in the Original Name field

### Duplicate Pirate
**Error:** "Failed to create pirate (may already exist)"
**Trigger:** Trying to create a pirate with an original name that already exists in that expedition
**Solution:** Use a different original name or check if pirate already exists

### API Error
**Error:** "Failed to create pirate. Please try again."
**Trigger:** Server/network error during creation
**Solution:** Try again or check server logs

## Visual Feedback

### Success States
1. **Creating State:**
   - Button text changes to "Creating..."
   - Button becomes disabled
   - User cannot interact with form

2. **Success State:**
   - Modal closes automatically
   - New pirate appears in the table below
   - Haptic feedback (on mobile devices)
   - Pirate name is highlighted

### Error States
- Red warning banner appears above action buttons
- Contains error icon (⚠️) and error message
- Form remains open for correction

## Keyboard Shortcuts
- **Escape:** Close modal
- **Enter:** Submit form (when in text input)

## Mobile Responsiveness
- Modal adjusts to screen size
- Form inputs stack vertically on small screens
- Touch-friendly button sizes
- Dropdown optimized for mobile selection

## Integration with Existing Features

### After Creation
The newly created pirate will:
1. **Appear in the table** - Immediately visible in the pirates list
2. **Be available for consumption** - Can be used in expedition item tracking
3. **Support decryption** - If expedition has owner key, original name can be decrypted
4. **Follow anonymization rules** - Same privacy rules as auto-created pirates

### Permission Requirements
**Required Permission:** Owner or Admin level
- Users without proper permission won't see the Create button
- API will reject requests from non-admin users

## Tips for Best Use

1. **Use Auto-Generation:** Leave pirate name blank for consistent naming
2. **Check Duplicates:** Review existing pirates before creating new ones
3. **Active Expeditions Only:** Only active expeditions appear in dropdown
4. **Original Name Privacy:** Original names are encrypted if expedition has owner key

## Troubleshooting

### Button Not Visible
- **Cause:** Insufficient permissions
- **Solution:** Log in as Owner or Admin

### No Expeditions in Dropdown
- **Cause:** No active expeditions exist
- **Solution:** Create an expedition first or check expedition status

### Pirate Not Appearing After Creation
- **Cause:** May be on different page or filtered out
- **Solution:** Refresh the page or check filtering settings

---

**Last Updated:** 2025-10-16
**Related Documentation:** [pirate_creation_feature.md](pirate_creation_feature.md)
