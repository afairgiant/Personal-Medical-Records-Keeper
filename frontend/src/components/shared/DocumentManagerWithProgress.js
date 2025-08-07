import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  Stack,
  Alert,
} from '@mantine/core';
import {
  IconAlertTriangle,
} from '@tabler/icons-react';
import useDocumentManagerCore from './DocumentManagerCore';
import ProgressTracking from './ProgressTracking';
import RenderModeContent from './RenderModeContent';
import DocumentManagerErrorBoundary from './DocumentManagerErrorBoundary';


// Inner component that can use hooks
const DocumentManagerContent = React.memo(({
  entityType,
  entityId,
  mode,
  config,
  onFileCountChange,
  onError,
  onUploadComplete,
  onUploadPendingFiles,
  onBlockingStateChange,
  className,
  showProgressModal,
  progressProps
}) => {
  // Local state for modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [fileUpload, setFileUpload] = useState({ file: null, description: '' });

  // Refs to store handlers for stable callback functions
  const handlersRef = useRef(null);

  // Get handlers from DocumentManagerCore hook with progress props from ProgressTracking
  const coreHandlers = useDocumentManagerCore({
    entityType,
    entityId,
    mode,
    onFileCountChange,
    onError,
    onUploadComplete,
    showProgressModal,
    ...progressProps
  });

  // Performance optimization: Memoize form submission handler
  const handleFileUploadSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!fileUpload.file || !handlersRef.current) return;

    await handlersRef.current.handleImmediateUpload(fileUpload.file, fileUpload.description);
    setFileUpload({ file: null, description: '' });
    setShowUploadModal(false);
  }, [fileUpload.file, fileUpload.description]);

  // Update handlers ref when they change
  useEffect(() => {
    if (handlersRef.current !== coreHandlers) {
      handlersRef.current = coreHandlers;
      
      // Trigger parent callback update when handlers are ready
      if (onUploadPendingFiles && coreHandlers) {
        onUploadPendingFiles({
          uploadPendingFiles: coreHandlers.uploadPendingFiles,
          getPendingFilesCount: coreHandlers.getPendingFilesCount,
          hasPendingFiles: coreHandlers.hasPendingFiles,
          clearPendingFiles: coreHandlers.clearPendingFiles,
        });
      }
    }
  }, [coreHandlers, onUploadPendingFiles]);

  // Track blocking state from progress props and notify parent
  useEffect(() => {
    if (onBlockingStateChange && progressProps.uploadState) {
      const isBlocking = !progressProps.uploadState.canClose;
      onBlockingStateChange(isBlocking);
    }
  }, [progressProps.uploadState?.canClose, onBlockingStateChange]);

  return (
    <Stack gap="md" className={className}>
      {/* Error Display */}
      {coreHandlers.error && (
        <Alert
          variant="light"
          color="red"
          title="File Operation Error"
          icon={<IconAlertTriangle size={16} />}
          withCloseButton
          onClose={() => coreHandlers.setError('')}
        >
          {coreHandlers.error}
        </Alert>
      )}

      {/* Main Content */}
      <DocumentManagerErrorBoundary
        componentName="DocumentManager Content"
        onError={onError}
      >
        <RenderModeContent
          mode={mode}
          loading={coreHandlers.loading}
          files={coreHandlers.files}
          paperlessLoading={coreHandlers.paperlessLoading}
          selectedStorageBackend={coreHandlers.selectedStorageBackend}
          onStorageBackendChange={coreHandlers.setSelectedStorageBackend}
          paperlessSettings={coreHandlers.paperlessSettings}
          syncStatus={coreHandlers.syncStatus}
          syncLoading={coreHandlers.syncLoading}
          pendingFiles={coreHandlers.pendingFiles}
          filesToDelete={coreHandlers.filesToDelete}
          config={config}
          // Upload functionality - these are the expected prop names
          onAddPendingFile={coreHandlers.handleAddPendingFile}
          onRemovePendingFile={coreHandlers.handleRemovePendingFile}
          onPendingFileDescriptionChange={coreHandlers.handlePendingFileDescriptionChange}
          onUploadPendingFiles={coreHandlers.uploadPendingFiles}
          onUploadModalOpen={setShowUploadModal}
          onCheckSyncStatus={coreHandlers.handleCheckSyncStatus}
          // File operations - these are the expected prop names  
          onDownloadFile={coreHandlers.handleDownloadFile}
          onViewFile={coreHandlers.handleViewFile}
          onImmediateDelete={coreHandlers.handleImmediateDelete}
          onMarkFileForDeletion={coreHandlers.handleMarkFileForDeletion}
          onUnmarkFileForDeletion={coreHandlers.handleUnmarkFileForDeletion}
        />
      </DocumentManagerErrorBoundary>
    </Stack>
  );
});


const DocumentManagerWithProgress = React.memo(({
  entityType,
  entityId,
  mode = 'view', // 'view', 'edit', 'create'
  config = {},
  onFileCountChange,
  onError,
  onUploadPendingFiles, // Callback to expose upload function
  className = '',
  showProgressModal = true, // Whether to show the progress modal
  onUploadComplete, // Callback when upload completes
  onBlockingStateChange, // Callback when blocking state changes
}) => {
  return (
    <ProgressTracking
      showProgressModal={showProgressModal}
      onUploadComplete={onUploadComplete}
    >
      {(progressProps) => (
        <DocumentManagerContent
          entityType={entityType}
          entityId={entityId}
          mode={mode}
          config={config}
          onFileCountChange={onFileCountChange}
          onError={onError}
          onUploadComplete={onUploadComplete}
          onUploadPendingFiles={onUploadPendingFiles}
          onBlockingStateChange={onBlockingStateChange}
          className={className}
          showProgressModal={showProgressModal}
          progressProps={progressProps}
        />
      )}
    </ProgressTracking>
  );
}, (prevProps, nextProps) => {
  // Only re-render if essential props change
  return (
    prevProps.entityType === nextProps.entityType &&
    prevProps.entityId === nextProps.entityId &&
    prevProps.mode === nextProps.mode &&
    prevProps.showProgressModal === nextProps.showProgressModal &&
    prevProps.onUploadComplete === nextProps.onUploadComplete &&
    JSON.stringify(prevProps.config) === JSON.stringify(nextProps.config)
  );
});

export default DocumentManagerWithProgress;