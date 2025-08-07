# Document Upload Refactoring - Complete Implementation Guide

## Overview
Extracting document upload functionality from 4 medical entities (Lab Results, Insurance, Procedures, Visits) into a single reusable component to eliminate code duplication and ensure consistency.

## Current Implementation Analysis

### Pattern 1: View Modals (4 files)
**Structure**: `Card` → `Stack` → `Text("ATTACHED DOCUMENTS")` → `Divider` → `DocumentManagerWithProgress`

1. **LabResultViewModal.js** (lines 207-227)
   - Uses: mode="view", extensive file types, structured error logging
   - Props: `onUploadComplete`, `onError={handleDocumentError}`
   
2. **InsuranceViewModal.js** (lines 216-237)  
   - Uses: mode="view", extensive file types, simpler error handling
   - Props: `onUploadComplete`, `onError`
   
3. **ProcedureViewModal.js** (lines 312-332)
   - Uses: mode="view", extensive file types, medium error handling
   - Props: `onUploadComplete={handleDocumentUploadComplete}`, `onError={handleDocumentError}`
   
4. **VisitViewModal.js** (lines 368-388)
   - Uses: mode="view", LIMITED file types (.pdf, .jpg, .jpeg, .png, .doc, .docx)
   - Props: `onUploadComplete={handleDocumentUploadComplete}`, `onError={handleDocumentError}`

### Pattern 2: Edit Forms (4 files)
**Structure**: `Paper` → `Title(conditional)` → `DocumentManagerWithProgress`

1. **LabResultFormWrapper.js** (lines 74-97)
   - Uses: mode="edit", conditional entityId, Card wrapper (different from others)
   - Title: "ATTACHED DOCUMENTS" (static)
   - **UNIQUE**: Only shows when `editingItem` exists
   
2. **ProcedureFormWrapper.js** (lines 70-89)
   - Uses: mode={editingItem ? 'edit' : 'create'}, Paper wrapper
   - Title: `{editingItem ? 'Manage Files' : 'Add Files (Optional)'}`
   - Props: `onUploadPendingFiles={handleDocumentManagerRef}`
   
3. **VisitFormWrapper.js** (lines 72-91)
   - Uses: mode={editingItem ? 'edit' : 'create'}, Paper wrapper  
   - Title: `{editingItem ? 'Manage Files' : 'Add Files (Optional)'}`
   - Props: `onUploadPendingFiles={handleDocumentManagerRef}`
   
4. **Insurance.js** (lines 704-729) - **EMBEDDED IN PAGE**
   - Uses: mode={editingInsurance ? 'edit' : 'create'}, Paper wrapper
   - Title: `{editingInsurance ? 'Manage Files' : 'Add Files (Optional)'}`  
   - Props: `onUploadPendingFiles={setDocumentManagerMethods}`

## Critical Integration Points

### 1. Form Submission Coordination
- **Key Prop**: `onUploadPendingFiles={callback}`
- **Provides Methods**: `{uploadPendingFiles, getPendingFilesCount, hasPendingFiles, clearPendingFiles}`
- **Usage**: Forms call these during submission via `useFormSubmissionWithUploads` hook
- **Sequence**: Form data submitted → Files uploaded → Complete

### 2. Progress System Components
- **ProgressTracking**: Wraps DocumentManagerWithProgress
- **UploadProgressModal**: Real-time progress display
- **useUploadProgress**: State management hook
- **Features**: File-by-file status, overall progress, time estimates, retry functionality

### 3. Error Handling Layers
- **DocumentManagerErrorBoundary**: Component-level error catching
- **UploadProgressErrorBoundary**: Progress modal error catching  
- **Structured Logging**: Entity-specific context (labResultId, procedureId, etc.)
- **Error Display**: Alert components with dismissible messages

### 4. File Configuration Standards
- **Lab Results**: ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.txt', '.csv', '.xml', '.json', '.doc', '.docx', '.xls', '.xlsx']
- **Insurance**: ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.txt', '.csv', '.xml', '.json', '.doc', '.docx', '.xls', '.xlsx']  
- **Procedures**: ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif', '.txt', '.csv', '.xml', '.json', '.doc', '.docx', '.xls', '.xlsx']
- **Visits**: ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'] ← **MORE RESTRICTIVE**
- **Standard**: 10MB max, 10 files max

## Implementation Plan

### Phase 1: Create DocumentSection Component
**File**: `frontend/src/components/shared/DocumentSection.js`

**Props Interface**:
```javascript
DocumentSection({
  // Core functionality
  entityType: string,           // "lab-result", "insurance", "procedure", "visit"
  entityId: string|null,        // Can be null for create mode
  mode: "view"|"edit"|"create", // Determines UI and behavior
  
  // Upload coordination (required for forms)
  onUploadPendingFiles: func,   // Callback for form integration
  
  // Event handlers
  onUploadComplete: func,       // Upload completion callback
  onError: func,               // Error handling callback
  
  // UI customization
  title: string,               // Optional, defaults based on mode
  wrapper: "card"|"paper",     // Optional, auto-detected from mode
  showProgressModal: bool,     // Optional, defaults to true
  
  // File configuration
  config: object,              // Optional, uses entity defaults
})
```

**Internal Logic**:
- Auto-detect wrapper: view="card", edit/create="paper"
- Auto-detect title: view="ATTACHED DOCUMENTS", edit/create=conditional
- Preserve all progress tracking and error handling
- Entity-specific file type configurations

### Phase 2: Update All Implementations

#### View Modals (Simple Replacements)
```javascript
// Replace existing Card+Stack+Text+Divider+DocumentManagerWithProgress with:
<DocumentSection
  entityType="lab-result"
  entityId={entity.id}
  mode="view"
  onUploadComplete={onUploadComplete}
  onError={onError}
/>
```

#### Edit Forms (Complex Replacements)  
```javascript
// Replace existing Paper+Title+DocumentManagerWithProgress with:
<DocumentSection
  entityType="procedure" 
  entityId={editingItem?.id}
  mode={editingItem ? 'edit' : 'create'}
  onUploadPendingFiles={setDocumentManagerMethods}
  onUploadComplete={onUploadComplete}
  onError={onError}
/>
```

### Phase 3: File Updates Required

**View Modals**:
1. `frontend/src/components/medical/labresults/LabResultViewModal.js` (lines 207-227)
2. `frontend/src/components/medical/insurance/InsuranceViewModal.js` (lines 216-237)
3. `frontend/src/components/medical/procedures/ProcedureViewModal.js` (lines 312-332)
4. `frontend/src/components/medical/visits/VisitViewModal.js` (lines 368-388)

**Edit Forms**:
5. `frontend/src/components/medical/labresults/LabResultFormWrapper.js` (lines 74-97)
6. `frontend/src/components/medical/procedures/ProcedureFormWrapper.js` (lines 70-89)
7. `frontend/src/components/medical/visits/VisitFormWrapper.js` (lines 72-91)
8. `frontend/src/pages/medical/Insurance.js` (lines 704-729)

### Phase 4: Testing Strategy

**Functional Testing**:
- [ ] View modal document display works for all 4 entities
- [ ] Edit form upload coordination works with form submission
- [ ] Create mode works with null entityId
- [ ] Progress modal displays correctly during uploads
- [ ] Error handling works at all levels
- [ ] File type restrictions work correctly
- [ ] Retry functionality works for failed uploads

**Integration Testing**:
- [ ] Form submission + upload coordination works
- [ ] File count updates work in parent pages
- [ ] Modal blocking works during uploads
- [ ] All error states display correctly
- [ ] Progress tracking state management works

**Visual Testing**:
- [ ] Card wrapper displays correctly in view modals
- [ ] Paper wrapper displays correctly in edit forms  
- [ ] Titles display correctly (static vs conditional)
- [ ] Progress bars and status icons work
- [ ] Error messages display properly

## Success Criteria
- [ ] All 8+ locations use DocumentSection component
- [ ] Zero functional regressions
- [ ] Identical visual appearance 
- [ ] All upload processes work identically
- [ ] Code duplication eliminated
- [ ] Future entities can easily add document support

## Rollback Plan
- Keep original files as .backup during development
- Test each replacement individually
- If issues found, revert specific files while continuing with others