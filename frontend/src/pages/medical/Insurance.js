import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMedicalData } from '../../hooks/useMedicalData';
import { useDataManagement } from '../../hooks/useDataManagement';
import { apiService } from '../../services/api';
import { formatDate } from '../../utils/helpers';
import { getMedicalPageConfig } from '../../utils/medicalPageConfigs';
import { usePatientWithStaticData } from '../../hooks/useGlobalData';
import { getEntityFormatters } from '../../utils/tableFormatters';
import { navigateToEntity } from '../../utils/linkNavigation';
import { cleanPhoneNumber, formatPhoneNumber } from '../../utils/phoneUtils';
import { 
  initializeFormData as initFormData, 
  restructureFormData, 
  insuranceFieldConfig, 
  insuranceDefaultValues 
} from '../../utils/nestedFormUtils';
import { printInsuranceRecord } from '../../utils/printTemplateGenerator';
import logger from '../../services/logger';
import { notifications } from '@mantine/notifications';
import { 
  ERROR_MESSAGES, 
  SUCCESS_MESSAGES,
  getUserFriendlyError
} from '../../constants/errorMessages';
import { PageHeader } from '../../components';
import MantineFilters from '../../components/mantine/MantineFilters';
import MedicalTable from '../../components/shared/MedicalTable';
import ViewToggle from '../../components/shared/ViewToggle';
import StatusBadge from '../../components/medical/StatusBadge';
import InsuranceCard from '../../components/medical/insurance/InsuranceCard';
import InsuranceFormWrapper from '../../components/medical/insurance/InsuranceFormWrapper';
import InsuranceViewModal from '../../components/medical/insurance/InsuranceViewModal';
import DocumentSection from '../../components/shared/DocumentSection';
import FormLoadingOverlay from '../../components/shared/FormLoadingOverlay';
import { useFormSubmissionWithUploads } from '../../hooks/useFormSubmissionWithUploads';
import {
  Badge,
  Button,
  Card,
  Group,
  Stack,
  Text,
  Grid,
  Container,
  Alert,
  Loader,
  Center,
  Divider,
  Modal,
  Title,
  Paper,
} from '@mantine/core';

const Insurance = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [viewMode, setViewMode] = useState('cards');

  // Modern data management with useMedicalData
  const {
    items: insurances = [],
    currentPatient,
    loading = false,
    error,
    createItem = async () => {},
    updateItem = async () => {},
    deleteItem = async () => {},
    refreshData = () => {},
  } = useMedicalData({
    entityName: 'insurance',
    apiMethodsConfig: {
      getAll: signal => apiService.getInsurances(signal),
      getByPatient: (patientId, signal) =>
        apiService.getPatientInsurances(patientId, signal),
      create: (data, signal) => apiService.createInsurance(data, signal),
      update: (id, data, signal) =>
        apiService.updateInsurance(id, data, signal),
      delete: (id, signal) => apiService.deleteInsurance(id, signal),
    },
    requiresPatient: true,
  }) || {};

  // Get configuration for filtering and sorting
  const config = getMedicalPageConfig('insurances');

  // File count management for cards
  const [fileCounts, setFileCounts] = useState({});
  const [fileCountsLoading, setFileCountsLoading] = useState({});

  // Track if we need to refresh after form submission (but not after uploads)
  const needsRefreshAfterSubmissionRef = useRef(false);

  // Form submission with uploads hook
  const {
    submissionState,
    startSubmission,
    completeFormSubmission,
    startFileUpload,
    completeFileUpload,
    handleSubmissionFailure,
    resetSubmission,
    isBlocking,
    canSubmit,
    statusMessage,
  } = useFormSubmissionWithUploads({
    entityType: 'insurance',
    onSuccess: () => {
      // Reset form and close modal on complete success
      setIsFormOpen(false);
      setEditingInsurance(null);
      setFormData(initializeFormData());
      
      // Only refresh if we created a new insurance during form submission
      // Don't refresh after uploads complete to prevent resource exhaustion
      if (needsRefreshAfterSubmissionRef.current) {
        needsRefreshAfterSubmissionRef.current = false;
        refreshData();
      }
    },
    onError: (error) => {
      logger.error('insurance_form_error', {
        message: 'Form submission error in insurance',
        error,
        component: 'Insurance',
      });
    },
    component: 'Insurance',
  });

  // Data management (filtering, sorting, pagination)
  const dataManagement = useDataManagement(insurances || [], config) || {};
  
  const {
    data: processedInsurances = [],
    filters = {},
    updateFilter = () => {},
    clearFilters = () => {},
    hasActiveFilters = false,
    statusOptions = [],
    categoryOptions = [],
    dateRangeOptions = [],
    sortOptions = [],
    handleSortChange = () => {},
    sortBy = '',
    sortOrder = 'asc',
    getSortIndicator = () => '',
    totalCount = 0,
    filteredCount = 0,
  } = dataManagement;

  // Form state management
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingInsurance, setEditingInsurance] = useState(null);
  const [formData, setFormData] = useState({});

  // View modal state management
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingInsurance, setViewingInsurance] = useState(null);

  // Document management state
  const [documentManagerMethods, setDocumentManagerMethods] = useState(null);
  const [viewDocumentManagerMethods, setViewDocumentManagerMethods] = useState(null);

  // Function to refresh file counts for all insurances
  const refreshFileCount = useCallback(async (insuranceId) => {
    try {
      const files = await apiService.getEntityFiles('insurance', insuranceId);
      const count = Array.isArray(files) ? files.length : 0;
      setFileCounts(prev => ({ ...prev, [insuranceId]: count }));
    } catch (error) {
      console.error(`Error refreshing file count for insurance ${insuranceId}:`, error);
    }
  }, []);

  // Load file counts for insurances
  useEffect(() => {
    const loadFileCountsForInsurances = async () => {
      if (!insurances || insurances.length === 0) return;
      
      const countPromises = insurances.map(async (insurance) => {
        setFileCountsLoading(prev => {
          if (prev[insurance.id] !== undefined) return prev; // Already loading
          return { ...prev, [insurance.id]: true };
        });
        
        try {
          const files = await apiService.getEntityFiles('insurance', insurance.id);
          const count = Array.isArray(files) ? files.length : 0;
          setFileCounts(prev => ({ ...prev, [insurance.id]: count }));
        } catch (error) {
          console.error(`Error loading file count for insurance ${insurance.id}:`, error);
          setFileCounts(prev => ({ ...prev, [insurance.id]: 0 }));
        } finally {
          setFileCountsLoading(prev => ({ ...prev, [insurance.id]: false }));
        }
      });
      
      await Promise.all(countPromises);
    };

    loadFileCountsForInsurances();
  }, [insurances]); // Remove fileCounts from dependencies

  // Table formatters - consistent with medication table approach
  const formatters = {
    insurance_type: (value, item) => (
      <Badge
        variant="light"
        color={
          item.insurance_type === 'medical' ? 'blue' :
          item.insurance_type === 'dental' ? 'green' :
          item.insurance_type === 'vision' ? 'purple' : 'orange'
        }
      >
        {item.insurance_type?.charAt(0).toUpperCase() + item.insurance_type?.slice(1)}
      </Badge>
    ),
    company_name: (value, item) => (
      <div>
        <Text weight={500}>{item.company_name}</Text>
        {item.plan_name && <Text size="xs" color="dimmed">{item.plan_name}</Text>}
      </div>
    ),
    member_name: (value, item) => (
      <div>
        <Text>{item.member_name}</Text>
        <Text size="xs" color="dimmed">ID: {item.member_id}</Text>
      </div>
    ),
    effective_date: (value, item) => (
      <div>
        <Text size="sm">
          {formatDate(item.effective_date)} - {item.expiration_date ? formatDate(item.expiration_date) : 'Ongoing'}
        </Text>
      </div>
    ),
    status: (value, item) => <StatusBadge status={item.status} />,
    is_primary: (value, item) => {
      if (item.insurance_type === 'medical' && value) {
        return 'PRIMARY';
      }
      return '';
    },
  };

  // Table configuration - consistent with medication table approach
  const tableColumns = [
    {
      accessor: 'insurance_type',
      header: 'Type',
      sortable: true,
    },
    {
      accessor: 'company_name',
      header: 'Company',
      sortable: true,
    },
    {
      accessor: 'member_name',
      header: 'Member',
      sortable: true,
    },
    {
      accessor: 'effective_date',
      header: 'Coverage Period',
      sortable: true,
    },
    {
      accessor: 'status',
      header: 'Status',
      sortable: true,
    },
    {
      accessor: 'is_primary',
      header: 'Primary',
    },
  ];

  // Initialize form data using utility
  const initializeFormData = (insurance = null) => {
    return initFormData(insurance, insuranceFieldConfig, insuranceDefaultValues);
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Start submission immediately to prevent race conditions
    startSubmission();

    if (!canSubmit) {
      logger.warn('insurance_race_condition_prevented', {
        message: 'Form submission prevented due to race condition',
        component: 'Insurance',
      });
      return;
    }

    try {
      // Use utility to restructure form data
      const submitData = restructureFormData(formData, insuranceFieldConfig);
      
      // Add patient_id to the form data (like medication does)
      submitData.patient_id = currentPatient.id;

      let success;
      let resultId;

      // Submit form data
      if (editingInsurance) {
        logger.info('Updating insurance', {
          insuranceId: editingInsurance.id,
          insurance_type: formData.insurance_type,
          company: formData.company_name
        });
        success = await updateItem(editingInsurance.id, submitData);
        resultId = editingInsurance.id;
        // No refresh needed for updates - user stays on same page
      } else {
        logger.info('Creating new insurance', {
          insurance_type: formData.insurance_type,
          company: formData.company_name
        });
        const result = await createItem(submitData);
        success = !!result;
        resultId = result?.id;
        // Set flag to refresh after new insurance creation (but only after form submission, not uploads)
        if (success) {
          needsRefreshAfterSubmissionRef.current = true;
          // Immediately refresh data to ensure new record appears
          await refreshData();
        }
      }

      // Complete form submission
      completeFormSubmission(success, resultId);

      if (success && resultId) {
        // Check if we have files to upload
        const hasPendingFiles = documentManagerMethods?.hasPendingFiles?.();
        
        if (hasPendingFiles) {
          logger.info('insurance_starting_file_upload', {
            message: 'Starting file upload process',
            insuranceId: resultId,
            pendingFilesCount: documentManagerMethods.getPendingFilesCount(),
            component: 'Insurance',
          });

          // Start file upload process
          startFileUpload();

          try {
            // Upload files with progress tracking
            await documentManagerMethods.uploadPendingFiles(resultId);
            
            // File upload completed successfully
            completeFileUpload(true, documentManagerMethods.getPendingFilesCount(), 0);
            
            // Refresh file count
            refreshFileCount(resultId);
          } catch (uploadError) {
            logger.error('insurance_file_upload_error', {
              message: 'File upload failed',
              insuranceId: resultId,
              error: uploadError.message,
              component: 'Insurance',
            });
            
            // File upload failed
            completeFileUpload(false, 0, documentManagerMethods.getPendingFilesCount());
          }
        } else {
          // No files to upload, complete immediately
          completeFileUpload(true, 0, 0);
        }
      }
    } catch (error) {
      logger.error('insurance_submission_error', {
        message: 'Form submission failed',
        error: error.message,
        component: 'Insurance',
      });
      
      // Check if it's a validation error
      if (error.validationErrors) {
        handleSubmissionFailure(error.validationErrors.join('\n'), 'form');
      } else {
        handleSubmissionFailure(error, 'form');
      }
    }
  };

  // Handle edit
  const handleEdit = (insurance) => {
    try {
      const initialFormData = initializeFormData(insurance);
      
      setEditingInsurance(insurance);
      setFormData(initialFormData);
      setIsFormOpen(true);
    } catch (error) {
      logger.error('Error initiating insurance edit:', error);
      notifications.show({
        title: 'Error',
        message: ERROR_MESSAGES.UNKNOWN_ERROR,
        color: 'red',
      });
    }
  };

  // Handle delete
  const handleDelete = async (insuranceOrId) => {
    // Handle both ID (from table) and full object (from card)
    const insuranceId = typeof insuranceOrId === 'object' ? insuranceOrId.id : insuranceOrId;
    const insurance = typeof insuranceOrId === 'object' ? insuranceOrId : 
      insurances.find(i => i.id === insuranceOrId);
    
    if (!insurance) {
      notifications.show({
        title: 'Error',
        message: ERROR_MESSAGES.ENTITY_NOT_FOUND,
        color: 'red',
      });
      return;
    }

    if (window.confirm(`Are you sure you want to delete this ${insurance.insurance_type} insurance?`)) {
      const success = await deleteItem(insuranceId);
      // Note: deleteItem already updates local state, no need to refresh all data
      // The useMedicalData hook handles state updates automatically
      if (success) {
        // Only refresh file counts as they might be affected by deletion
        setFileCounts(prev => {
          const updated = { ...prev };
          delete updated[insuranceId];
          return updated;
        });
        setFileCountsLoading(prev => {
          const updated = { ...prev };
          delete updated[insuranceId];
          return updated;
        });
      }
    }
  };

  // Handle set primary
  const handleSetPrimary = async (insurance) => {
    try {
      logger.info('Setting insurance as primary', {
        insurance_id: insurance.id,
        insurance_type: insurance.insurance_type,
        company: insurance.company_name,
      });

      await apiService.setPrimaryInsurance(insurance.id);
      
      notifications.show({
        title: 'Primary Insurance Set',
        message: `${insurance.company_name} is now your primary ${insurance.insurance_type} insurance`,
        color: 'green',
      });

      // Refresh data to show updated primary status
      await refreshData();

      logger.info('Primary insurance set successfully', {
        insurance_id: insurance.id,
        insurance_type: insurance.insurance_type,
      });
    } catch (error) {
      logger.error('Error setting primary insurance:', error);
      notifications.show({
        title: 'Error',
        message: ERROR_MESSAGES.SERVER_ERROR,
        color: 'red',
      });
    }
  };

  // Handle add new
  const handleAddNew = () => {
    resetSubmission(); // Reset submission state
    setEditingInsurance(null);
    setDocumentManagerMethods(null); // Reset document manager methods
    setFormData(initializeFormData());
    setIsFormOpen(true);
  };

  // Handle close form
  const handleCloseForm = () => {
    // Prevent closing during upload
    if (isBlocking) {
      return;
    }
    
    resetSubmission(); // Reset submission state
    setIsFormOpen(false);
    setEditingInsurance(null);
    setDocumentManagerMethods(null); // Reset document manager methods
    setFormData(initializeFormData());
  };

  // Handle view insurance
  const handleViewInsurance = (insurance) => {
    try {
      setViewingInsurance(insurance);
      setShowViewModal(true);
      
      // Add view parameter to URL for deep linking
      const searchParams = new URLSearchParams(location.search);
      searchParams.set('view', insurance.id);
      navigate({ search: searchParams.toString() }, { replace: true });
    } catch (error) {
      logger.error('Error opening insurance view modal:', error);
      notifications.show({
        title: 'Error',
        message: ERROR_MESSAGES.ENTITY_NOT_FOUND,
        color: 'red',
      });
    }
  };

  // Handle close view modal
  const handleCloseViewModal = () => {
    // Refresh file count for the viewed insurance before closing
    if (viewingInsurance) {
      refreshFileCount(viewingInsurance.id);
    }
    
    setShowViewModal(false);
    setViewingInsurance(null);
    
    // Remove view parameter from URL
    const searchParams = new URLSearchParams(location.search);
    searchParams.delete('view');
    navigate({ search: searchParams.toString() }, { replace: true });
  };

  // Handle URL view parameter for deep linking
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const viewId = searchParams.get('view');
    
    if (viewId && insurances.length > 0 && !loading) {
      const insurance = insurances.find(i => i.id.toString() === viewId);
      if (insurance && !showViewModal) {
        // Only auto-open if modal isn't already open
        setViewingInsurance(insurance);
        setShowViewModal(true);
      }
    }
  }, [location.search, insurances, loading, showViewModal]);

  // Loading state
  if (loading) {
    return (
      <Container size="xl">
        <Center style={{ height: 400 }}>
          <Loader size="lg" />
        </Center>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container size="xl">
        <Alert color="red" title="Error loading insurance records">
          {getUserFriendlyError(error, 'load')}
        </Alert>
      </Container>
    );
  }

  return (
    <Container size="xl">
      <PageHeader
        title="Insurance"
        description="Manage your insurance information and digital cards"
      />

      <Group justify="space-between" align="center">
        <Button variant="filled" onClick={handleAddNew}>
          + Add New Insurance
        </Button>

        <ViewToggle
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          showPrint={true}
        />
      </Group>

      {/* Mantine Filter Controls */}
      <MantineFilters
        filters={filters}
        updateFilter={updateFilter}
        clearFilters={clearFilters}
        hasActiveFilters={hasActiveFilters}
        statusOptions={statusOptions}
        categoryOptions={categoryOptions}
        dateRangeOptions={dateRangeOptions}
        sortOptions={sortOptions}
        sortBy={sortBy}
        sortOrder={sortOrder}
        handleSortChange={handleSortChange}
        totalCount={totalCount}
        filteredCount={filteredCount}
        config={config.filterControls}
      />

      {processedInsurances.length === 0 ? (
        <Card withBorder p="xl">
          <Stack align="center" gap="md">
            <Text size="3rem">🏥</Text>
            <Text size="xl" fw={600}>
              No Insurance Found
            </Text>
            <Text ta="center" c="dimmed">
              {hasActiveFilters
                ? 'Try adjusting your search or filter criteria.'
                : 'Start by adding your first insurance.'}
            </Text>
            {!hasActiveFilters && (
              <Button variant="filled" onClick={handleAddNew}>
                Add Your First Insurance
              </Button>
            )}
          </Stack>
        </Card>
      ) : (
        <>
          {viewMode === 'cards' ? (
            <Grid>
              {processedInsurances.map((insurance) => (
                <Grid.Col key={insurance.id} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
                  <InsuranceCard
                    insurance={insurance}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onSetPrimary={handleSetPrimary}
                    onView={handleViewInsurance}
                    fileCount={fileCounts[insurance.id] || 0}
                    fileCountLoading={fileCountsLoading[insurance.id] || false}
                  />
                </Grid.Col>
              ))}
            </Grid>
          ) : (
            <MedicalTable
              data={processedInsurances}
              columns={tableColumns}
              formatters={formatters}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onView={handleViewInsurance}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSortChange={handleSortChange}
              getSortIndicator={getSortIndicator}
            />
          )}
        </>
      )}

      {/* Form Modal */}
      <InsuranceFormWrapper
        isOpen={isFormOpen}
        onClose={() => {
          if (!isBlocking) {
            resetSubmission();
            setIsFormOpen(false);
            setEditingInsurance(null);
            setDocumentManagerMethods(null);
            setFormData(initializeFormData());
          }
        }}
        title={editingInsurance ? 'Edit Insurance' : 'Add New Insurance'}
        formData={formData}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
        editingItem={editingInsurance}
      >
        {/* Form Loading Overlay */}
        <FormLoadingOverlay
          visible={isBlocking}
          message={statusMessage?.title || 'Processing...'}
          submessage={statusMessage?.message}
          type={statusMessage?.type || 'loading'}
        />
        {/* File Management Section for Both Create and Edit Mode */}
        <DocumentSection
          entityType="insurance"
          entityId={editingInsurance?.id}
          mode={editingInsurance ? 'edit' : 'create'}
          onUploadPendingFiles={setDocumentManagerMethods}
          onError={(error) => {
            logger.error('document_manager_error', {
              message: `Document manager error in insurance ${editingInsurance ? 'edit' : 'create'}`,
              insuranceId: editingInsurance?.id,
              error: error,
              component: 'Insurance',
            });
          }}
        />
      </InsuranceFormWrapper>

      {/* View Modal */}
      <InsuranceViewModal
        isOpen={showViewModal}
        onClose={handleCloseViewModal}
        insurance={viewingInsurance}
        onEdit={handleEdit}
        onPrint={(insurance) => {
          printInsuranceRecord(
            insurance,
            () => {
              notifications.show({
                title: 'Print Ready',
                message: 'Complete insurance details sent to printer',
                color: 'blue',
              });
            },
            (error) => {
              notifications.show({
                title: 'Print Error',
                message: ERROR_MESSAGES.FILE_PROCESSING_FAILED,
                color: 'red',
              });
            }
          );
        }}
        onSetPrimary={handleSetPrimary}
        onFileUploadComplete={(success) => {
          if (success && viewingInsurance) {
            refreshFileCount(viewingInsurance.id);
          }
        }}
      />
    </Container>
  );
};

export default Insurance;