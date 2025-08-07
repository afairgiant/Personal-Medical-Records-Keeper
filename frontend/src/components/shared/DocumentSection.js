import React from 'react';
import { Card, Stack, Text, Divider, Paper, Title } from '@mantine/core';
import DocumentManagerWithProgress from './DocumentManagerWithProgress';

/**
 * DocumentSection - Unified component for document upload functionality
 * 
 * Eliminates code duplication across 8+ medical entity files by providing
 * a single component that handles both view modals and edit forms with
 * automatic wrapper and title detection based on mode.
 * 
 * Features:
 * - Auto-detection of wrapper (Card vs Paper) based on mode
 * - Auto-detection of titles based on mode and entityId
 * - Complete integration with existing upload progress system
 * - Preserves all error handling and logging functionality
 * - Standardized file configurations per entity type
 * 
 * @param {Object} props
 * @param {string} props.entityType - Entity type: "lab-result", "insurance", "procedure", "visit"
 * @param {string|null} props.entityId - Entity ID (can be null for create mode)
 * @param {string} props.mode - Mode: "view", "edit", "create"
 * @param {Function} [props.onUploadPendingFiles] - Required for forms - callback for upload coordination
 * @param {Function} [props.onUploadComplete] - Upload completion callback
 * @param {Function} [props.onError] - Error handling callback
 * @param {Function} [props.onFileCountChange] - File count change callback
 * @param {Function} [props.onBlockingStateChange] - Blocking state change callback for form coordination
 * @param {string} [props.title] - Custom title (auto-detected if not provided)
 * @param {string} [props.wrapper] - Wrapper type: "card"|"paper" (auto-detected if not provided)
 * @param {boolean} [props.showProgressModal=true] - Whether to show progress modal
 * @param {Object} [props.config] - File configuration (uses entity defaults if not provided)
 */
const DocumentSection = ({
  // Core functionality
  entityType,
  entityId,
  mode,
  
  // Upload coordination (required for forms)
  onUploadPendingFiles,
  
  // Event handlers
  onUploadComplete,
  onError,
  onFileCountChange,
  onBlockingStateChange,
  
  // UI customization (optional)
  title,
  wrapper,
  showProgressModal = true,
  
  // File configuration (optional)
  config,
  
  // Additional props to pass through
  ...additionalProps
}) => {
  // Auto-detect wrapper based on mode
  const autoWrapper = wrapper || (mode === 'view' ? 'card' : 'paper');
  
  // Auto-detect title based on mode and entityId
  const getAutoTitle = () => {
    if (title) return title;
    
    switch (mode) {
      case 'view':
        return 'ATTACHED DOCUMENTS';
      case 'edit':
        return entityId ? 'Manage Files' : 'Add Files (Optional)';
      case 'create':
        return 'Add Files (Optional)';
      default:
        return 'ATTACHED DOCUMENTS';
    }
  };
  
  // Entity-specific file configurations
  const getDefaultConfig = () => {
    if (config) return config;
    
    // Standard configuration for most entities
    const standardConfig = {
      acceptedTypes: [
        '.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif',
        '.txt', '.csv', '.xml', '.json', '.doc', '.docx', '.xls', '.xlsx'
      ],
      maxSize: 10 * 1024 * 1024, // 10MB
      maxFiles: 10
    };
    
    // Visits have more restrictive file types (preserve existing behavior)
    if (entityType === 'visit') {
      return {
        ...standardConfig,
        acceptedTypes: ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
      };
    }
    
    return standardConfig;
  };
  
  // Common DocumentManagerWithProgress props
  const documentManagerProps = {
    entityType,
    entityId,
    mode,
    config: getDefaultConfig(),
    showProgressModal,
    onUploadComplete,
    onError,
    onUploadPendingFiles,
    onFileCountChange,
    onBlockingStateChange,
    ...additionalProps
  };
  
  // Render view mode (Card wrapper)
  if (autoWrapper === 'card') {
    return (
      <Card withBorder>
        <Stack gap="sm">
          <Text fw={600} size="sm" c="dimmed">
            {getAutoTitle()}
          </Text>
          <Divider />
          <DocumentManagerWithProgress {...documentManagerProps} />
        </Stack>
      </Card>
    );
  }
  
  // Render edit/create mode (Paper wrapper)
  return (
    <Paper withBorder p="md" mt="md">
      <Title order={4} mb="md">
        {getAutoTitle()}
      </Title>
      <DocumentManagerWithProgress {...documentManagerProps} />
    </Paper>
  );
};

// Special handling for LabResult edit mode which uses Card wrapper
const DocumentSectionLabResultEdit = (props) => {
  // Only render for LabResult edit mode when editingItem exists
  if (props.entityType === 'lab-result' && props.mode === 'edit' && !props.entityId) {
    return null;
  }
  
  // Force Card wrapper for LabResult edit mode to match existing behavior
  if (props.entityType === 'lab-result' && props.mode === 'edit') {
    return (
      <DocumentSection 
        {...props} 
        wrapper="card" 
        title="ATTACHED DOCUMENTS" 
      />
    );
  }
  
  return <DocumentSection {...props} />;
};

export default DocumentSectionLabResultEdit;