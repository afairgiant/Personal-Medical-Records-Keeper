import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMedicalData } from '../../hooks/useMedicalData';
import { useDataManagement } from '../../hooks/useDataManagement';
import { apiService } from '../../services/api';
import { getMedicalPageConfig } from '../../utils/medicalPageConfigs';
import { usePatientWithStaticData } from '../../hooks/useGlobalData';
import { getEntityFormatters } from '../../utils/tableFormatters';
import { PageHeader } from '../../components';
import logger from '../../services/logger';
import MantineFilters from '../../components/mantine/MantineFilters';
import MedicalTable from '../../components/shared/MedicalTable';
import ViewToggle from '../../components/shared/ViewToggle';

// Modular components
import TreatmentCard from '../../components/medical/treatments/TreatmentCard';
import TreatmentViewModal from '../../components/medical/treatments/TreatmentViewModal';
import TreatmentFormWrapper from '../../components/medical/treatments/TreatmentFormWrapper';
import {
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
} from '@mantine/core';

const Treatments = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [viewMode, setViewMode] = useState('cards');

  // Get practitioners data
  const { practitioners: practitionersObject } =
    usePatientWithStaticData();

  const practitioners = practitionersObject?.practitioners || [];

  // Modern data management with useMedicalData
  const {
    items: treatments,
    currentPatient,
    loading,
    error,
    successMessage,
    createItem,
    updateItem,
    deleteItem,
    refreshData,
    clearError,
    setError,
  } = useMedicalData({
    entityName: 'treatment',
    apiMethodsConfig: {
      getAll: signal => apiService.getTreatments(signal),
      getByPatient: (patientId, signal) => apiService.getPatientTreatments(patientId, signal),
      create: (data, signal) => apiService.createTreatment(data, signal),
      update: (id, data, signal) =>
        apiService.updateTreatment(id, data, signal),
      delete: (id, signal) => apiService.deleteTreatment(id, signal),
    },
    requiresPatient: true,
  });

  // Conditions data for dropdown - following DRY principles with existing pattern
  const {
    items: conditions,
    loading: conditionsLoading,
    error: conditionsError,
  } = useMedicalData({
    entityName: 'conditionsDropdown',
    apiMethodsConfig: {
      getAll: signal => apiService.getConditions(signal),
      getByPatient: (patientId, signal) =>
        apiService.getPatientConditions(patientId, signal),
    },
    requiresPatient: true, // Get conditions for the current patient only
  });

  // Get standardized configuration
  const config = getMedicalPageConfig('treatments');

  // Use standardized data management
  const dataManagement = useDataManagement(treatments, config);

  // Form and UI state
  const [showModal, setShowModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingTreatment, setViewingTreatment] = useState(null);
  const [editingTreatment, setEditingTreatment] = useState(null);
  const [formData, setFormData] = useState({
    treatment_name: '',
    treatment_type: '',
    description: '',
    start_date: '',
    end_date: '',
    status: 'planned',
    dosage: '',
    frequency: '',
    notes: '',
    condition_id: '',
    practitioner_id: '',
  });

  const handleAddTreatment = () => {
    setEditingTreatment(null);
    setFormData({
      treatment_name: '',
      treatment_type: '',
      description: '',
      start_date: '',
      end_date: '',
      status: 'planned',
      dosage: '',
      frequency: '',
      notes: '',
      condition_id: '',
      practitioner_id: '',
    });
    setShowModal(true);
  };

  const handleEditTreatment = treatment => {
    setEditingTreatment(treatment);
    setFormData({
      treatment_name: treatment.treatment_name || '',
      treatment_type: treatment.treatment_type || '',
      description: treatment.description || '',
      start_date: treatment.start_date || '',
      end_date: treatment.end_date || '',
      status: treatment.status || 'planned',
      dosage: treatment.dosage || '',
      frequency: treatment.frequency || '',
      notes: treatment.notes || '',
      condition_id: treatment.condition_id ? String(treatment.condition_id) : '',
      practitioner_id: treatment.practitioner_id ? String(treatment.practitioner_id) : '',
    });
    setShowModal(true);
  };

  const handleViewTreatment = treatment => {
    // Use existing treatment data - no need to fetch again
    setViewingTreatment(treatment);
    setShowViewModal(true);
    // Update URL with treatment ID for sharing/bookmarking
    const searchParams = new URLSearchParams(location.search);
    searchParams.set('view', treatment.id);
    navigate(`${location.pathname}?${searchParams.toString()}`, {
      replace: true,
    });
  };

  const handleCloseViewModal = () => {
    setShowViewModal(false);
    setViewingTreatment(null);
    // Remove view parameter from URL
    const searchParams = new URLSearchParams(location.search);
    searchParams.delete('view');
    const newSearch = searchParams.toString();
    navigate(`${location.pathname}${newSearch ? `?${newSearch}` : ''}`, {
      replace: true,
    });
  };

  const handleDeleteTreatment = async treatmentId => {
    const success = await deleteItem(treatmentId);
    if (success) {
      await refreshData();
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    // Validation
    if (!formData.treatment_name.trim()) {
      setError('Treatment name is required');
      return;
    }

    if (!formData.treatment_type.trim()) {
      setError('Treatment type is required');
      return;
    }

    if (!formData.start_date) {
      setError('Start date is required');
      return;
    }

    if (
      formData.end_date &&
      formData.start_date &&
      new Date(formData.end_date) < new Date(formData.start_date)
    ) {
      setError('End date cannot be before start date');
      return;
    }

    if (!currentPatient?.id) {
      setError('Patient information not available');
      return;
    }

    const treatmentData = {
      treatment_name: formData.treatment_name,
      treatment_type: formData.treatment_type,
      description: formData.description,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
      status: formData.status,
      dosage: formData.dosage || null,
      frequency: formData.frequency || null,
      notes: formData.notes || null,
      patient_id: currentPatient.id,
      condition_id: formData.condition_id || null,
      practitioner_id: formData.practitioner_id || null,
    };

    let success;
    if (editingTreatment) {
      success = await updateItem(editingTreatment.id, treatmentData);
    } else {
      success = await createItem(treatmentData);
    }

    if (success) {
      setShowModal(false);
      await refreshData();
    }
  };

  const handleInputChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Helper functions moved to component files, keeping these for table formatters
  const getConditionName = conditionId => {
    if (!conditionId || !conditions || conditions.length === 0) {
      return null;
    }
    const condition = conditions.find(c => c.id === conditionId);
    return condition ? condition.diagnosis || condition.name : null;
  };

  const getPractitionerInfo = practitionerId => {
    if (
      !practitionerId ||
      !practitioners ||
      practitioners.length === 0
    ) {
      return null;
    }
    const practitioner = practitioners.find(
      p => p.id === practitionerId
    );
    return practitioner;
  };

  // Handler to navigate to condition page and open view modal
  const handleConditionClick = conditionId => {
    if (conditionId) {
      // Navigate to conditions page with view parameter to auto-open the modal
      navigate(`/conditions?view=${conditionId}`);
    }
  };

  // Handle URL parameters for direct linking to specific treatments
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const viewId = searchParams.get('view');

    if (viewId && treatments.length > 0 && !loading) {
      const treatment = treatments.find(t => t.id.toString() === viewId);
      if (treatment && !showViewModal) {
        // Only auto-open if modal isn't already open
        setViewingTreatment(treatment);
        setShowViewModal(true);
      }
    }
  }, [location.search, treatments, loading, showViewModal]);

  // Get processed data from data management
  const filteredTreatments = dataManagement.data;

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <Center h={200}>
          <Stack align="center">
            <Loader size="lg" />
            <Text>Loading treatments...</Text>
            <Text size="sm" c="dimmed">
              If this takes too long, please refresh the page
            </Text>
          </Stack>
        </Center>
      </Container>
    );
  }

  return (
    <>
      <Container size="xl" py="md">
        <PageHeader title="Treatments" icon="🩹" />

        <Stack gap="lg">
          {error && (
            <Alert
              variant="light"
              color="red"
              title="Error"
              withCloseButton
              onClose={clearError}
            >
              {error}
            </Alert>
          )}
          {conditionsError && (
            <Alert
              variant="light"
              color="orange"
              title="Conditions Loading Error"
            >
              {conditionsError}
            </Alert>
          )}
          {successMessage && (
            <Alert variant="light" color="green" title="Success">
              {successMessage}
            </Alert>
          )}

          <Group justify="space-between" align="center">
            <Button variant="filled" onClick={handleAddTreatment}>
              + Add Treatment
            </Button>

            <ViewToggle
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              showPrint={true}
            />
          </Group>

          {/* Mantine Filter Controls */}
          <MantineFilters
            filters={dataManagement.filters}
            updateFilter={dataManagement.updateFilter}
            clearFilters={dataManagement.clearFilters}
            hasActiveFilters={dataManagement.hasActiveFilters}
            statusOptions={dataManagement.statusOptions}
            categoryOptions={dataManagement.categoryOptions}
            dateRangeOptions={dataManagement.dateRangeOptions}
            sortOptions={dataManagement.sortOptions}
            sortBy={dataManagement.sortBy}
            sortOrder={dataManagement.sortOrder}
            handleSortChange={dataManagement.handleSortChange}
            totalCount={dataManagement.totalCount}
            filteredCount={dataManagement.filteredCount}
            config={config.filterControls}
          />

          {filteredTreatments.length === 0 ? (
            <Card withBorder p="xl">
              <Stack align="center" gap="md">
                <Text size="3rem">🩹</Text>
                <Text size="xl" fw={600}>
                  No Treatments Found
                </Text>
                <Text ta="center" c="dimmed">
                  {dataManagement.hasActiveFilters
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Start by adding your first treatment.'}
                </Text>
                {!dataManagement.hasActiveFilters && (
                  <Button variant="filled" onClick={handleAddTreatment}>
                    Add Your First Treatment
                  </Button>
                )}
              </Stack>
            </Card>
          ) : viewMode === 'cards' ? (
            <Grid>
              {filteredTreatments.map(treatment => (
                <Grid.Col key={treatment.id} span={{ base: 12, sm: 6, lg: 4 }}>
                  <TreatmentCard
                    treatment={treatment}
                    conditions={conditions}
                    onEdit={handleEditTreatment}
                    onDelete={handleDeleteTreatment}
                    onView={handleViewTreatment}
                    onConditionClick={handleConditionClick}
                    navigate={navigate}
                    onError={(error) => {
                      logger.error('TreatmentCard error', {
                        treatmentId: treatment.id,
                        error: error.message,
                        page: 'Treatments',
                      });
                    }}
                  />
                </Grid.Col>
              ))}
            </Grid>
          ) : (
            <MedicalTable
              data={filteredTreatments}
              columns={[
                { header: 'Treatment', accessor: 'treatment_name' },
                { header: 'Type', accessor: 'treatment_type' },
                { header: 'Practitioner', accessor: 'practitioner' },
                { header: 'Related Condition', accessor: 'condition' },
                { header: 'Start Date', accessor: 'start_date' },
                { header: 'End Date', accessor: 'end_date' },
                { header: 'Status', accessor: 'status' },
                { header: 'Dosage', accessor: 'dosage' },
                { header: 'Frequency', accessor: 'frequency' },
                { header: 'Notes', accessor: 'notes' },
              ]}
              patientData={currentPatient}
              tableName="Treatments"
              onView={handleViewTreatment}
              onEdit={handleEditTreatment}
              onDelete={handleDeleteTreatment}
              formatters={{
                treatment_name:
                  getEntityFormatters('treatments').treatment_name,
                treatment_type:
                  getEntityFormatters('treatments').treatment_type,
                practitioner: (value, row) => {
                  if (row.practitioner_id) {
                    const practitionerInfo = getPractitionerInfo(
                      row.practitioner_id
                    );
                    return `Dr. ${
                      row.practitioner?.name ||
                      practitionerInfo?.name ||
                      `#${row.practitioner_id}`
                    }`;
                  }
                  return 'No practitioner';
                },
                condition: (value, row) => {
                  if (row.condition_id) {
                    return (
                      row.condition?.diagnosis ||
                      getConditionName(row.condition_id) ||
                      `Condition #${row.condition_id}`
                    );
                  }
                  return 'No condition linked';
                },
                start_date: getEntityFormatters('treatments').start_date,
                end_date: getEntityFormatters('treatments').end_date,
                status: getEntityFormatters('treatments').status,
                dosage: getEntityFormatters('treatments').dosage,
                frequency: getEntityFormatters('treatments').frequency,
                notes: getEntityFormatters('treatments').notes,
              }}
            />
          )}
        </Stack>
      </Container>

      <TreatmentFormWrapper
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingTreatment ? 'Edit Treatment' : 'Add New Treatment'}
        editingTreatment={editingTreatment}
        formData={formData}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
        conditionsOptions={conditions}
        conditionsLoading={conditionsLoading}
        practitionersOptions={practitioners}
        practitionersLoading={false}
        isLoading={false}
      />

      <TreatmentViewModal
        isOpen={showViewModal}
        onClose={handleCloseViewModal}
        treatment={viewingTreatment}
        onEdit={handleEditTreatment}
        conditions={conditions}
        practitioners={practitioners}
        onConditionClick={handleConditionClick}
        navigate={navigate}
      />
    </>
  );
};

export default Treatments;
