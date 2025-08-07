import React from 'react';
import MantineProcedureForm from '../MantineProcedureForm';
import DocumentSection from '../../shared/DocumentSection';
import logger from '../../../services/logger';

const ProcedureFormWrapper = ({
  isOpen,
  onClose,
  title,
  formData,
  onInputChange,
  onSubmit,
  editingItem,
  practitioners,
  isLoading,
  statusMessage,
  onDocumentManagerRef,
  onFileUploadComplete,
  onError,
  children
}) => {
  const handleDocumentManagerRef = (methods) => {
    if (onDocumentManagerRef) {
      onDocumentManagerRef(methods);
    }
  };

  const handleDocumentError = (error) => {
    logger.error('document_manager_error', {
      message: `Document manager error in procedures ${editingItem ? 'edit' : 'create'}`,
      procedureId: editingItem?.id,
      error: error,
      component: 'ProcedureFormWrapper',
    });
    
    if (onError) {
      onError(error);
    }
  };

  const handleDocumentUploadComplete = (success, completedCount, failedCount) => {
    logger.info('procedures_upload_completed', {
      message: 'File upload completed in procedures form',
      procedureId: editingItem?.id,
      success,
      completedCount,
      failedCount,
      component: 'ProcedureFormWrapper',
    });
    
    if (onFileUploadComplete) {
      onFileUploadComplete(success, completedCount, failedCount);
    }
  };

  return (
    <MantineProcedureForm
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      formData={formData}
      onInputChange={onInputChange}
      onSubmit={onSubmit}
      practitioners={practitioners}
      editingProcedure={editingItem}
      isLoading={isLoading}
      statusMessage={statusMessage}
    >
      {/* File Management Section for Both Create and Edit Mode */}
      <DocumentSection
        entityType="procedure"
        entityId={editingItem?.id}
        mode={editingItem ? 'edit' : 'create'}
        onUploadPendingFiles={handleDocumentManagerRef}
        onUploadComplete={handleDocumentUploadComplete}
        onError={handleDocumentError}
      />
      
      {children}
    </MantineProcedureForm>
  );
};

export default ProcedureFormWrapper;