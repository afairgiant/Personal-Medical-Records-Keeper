import React from 'react';
import MantineLabResultForm from '../MantineLabResultForm';
import DocumentSection from '../../shared/DocumentSection';
import logger from '../../../services/logger';

const LabResultFormWrapper = ({
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
  onFileUploadComplete,
  conditions,
  labResultConditions,
  fetchLabResultConditions,
  navigate,
  currentPatient,
  onError,
  children
}) => {

  const handleDocumentError = (error) => {
    logger.error('document_manager_error', {
      message: `Document manager error in lab results ${editingItem ? 'edit' : 'create'}`,
      labResultId: editingItem?.id,
      error: error,
      component: 'LabResultFormWrapper',
    });
    
    if (onError) {
      onError(error);
    }
  };

  const handleDocumentUploadComplete = (success, completedCount, failedCount) => {
    logger.info('lab_results_upload_completed', {
      message: 'File upload completed in lab results form',
      labResultId: editingItem?.id,
      success,
      completedCount,
      failedCount,
      component: 'LabResultFormWrapper',
    });
    
    if (onFileUploadComplete) {
      onFileUploadComplete(success, completedCount, failedCount);
    }
  };

  return (
    <MantineLabResultForm
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      formData={formData}
      onInputChange={onInputChange}
      onSubmit={onSubmit}
      practitioners={practitioners}
      editingLabResult={editingItem}
      conditions={conditions}
      labResultConditions={labResultConditions}
      fetchLabResultConditions={fetchLabResultConditions}
      navigate={navigate}
      currentPatient={currentPatient}
      isLoading={isLoading}
      statusMessage={statusMessage}
    >
      {/* Document Management Section - Copied EXACTLY from view modal */}
      {editingItem && (
        <DocumentSection
          entityType="lab-result"
          entityId={editingItem.id}
          mode="edit"
          onUploadComplete={handleDocumentUploadComplete}
          onError={handleDocumentError}
        />
      )}
      
      {children}
    </MantineLabResultForm>
  );
};

export default LabResultFormWrapper;