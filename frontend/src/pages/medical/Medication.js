import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Button,
  Group,
  Stack,
  Text,
  Grid,
  Container,
  Alert,
  Loader,
  Center,
  Paper,
  Title,
} from '@mantine/core';
import {
  IconAlertTriangle,
  IconCheck,
  IconPlus,
} from '@tabler/icons-react';
import { useMedicalData } from '../../hooks/useMedicalData';
import { useDataManagement } from '../../hooks/useDataManagement';
import { apiService } from '../../services/api';
import { formatDate } from '../../utils/helpers';
import { getMedicalPageConfig } from '../../utils/medicalPageConfigs';
import { usePatientWithStaticData } from '../../hooks/useGlobalData';
import { getEntityFormatters } from '../../utils/tableFormatters';
import { navigateToEntity } from '../../utils/linkNavigation';
import { PageHeader } from '../../components';
import { ResponsiveTable } from '../../components/adapters';
import MantineFilters from '../../components/mantine/MantineFilters';
import ViewToggle from '../../components/shared/ViewToggle';
import { MedicationCard, MedicationViewModal, MedicationFormWrapper } from '../../components/medical/medications';
import { withResponsive } from '../../hoc/withResponsive';
import { useResponsive } from '../../hooks/useResponsive';
import logger from '../../services/logger';

const Medication = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const responsive = useResponsive();
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  
  // Form state - moved up to be available for refs logic
  const [showAddForm, setShowAddForm] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingMedication, setViewingMedication] = useState(null);
  const [editingMedication, setEditingMedication] = useState(null);

  // Get practitioners and pharmacies data
  const { practitioners: practitionersObject, pharmacies: pharmaciesObject } =
    usePatientWithStaticData();

  // Memoize practitioners and pharmacies to prevent unnecessary re-renders
  // Only recalculate when the actual data changes (not reference)
  const practitioners = useMemo(() => {
    const data = practitionersObject?.practitioners || [];
    logger.debug('Practitioners data updated', {
      component: 'Medication',
      practitionersCount: data.length
    });
    return data;
  }, [practitionersObject?.practitioners]);

  const pharmacies = useMemo(() => {
    const data = pharmaciesObject?.pharmacies || [];
    logger.debug('Pharmacies data updated', {
      component: 'Medication', 
      pharmaciesCount: data.length
    });
    return data;
  }, [pharmaciesObject?.pharmacies]);

  // Modern data management with useMedicalData
  const {
    items: medications,
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
    entityName: 'medication',
    apiMethodsConfig: {
      getAll: signal => apiService.getMedications(signal),
      getByPatient: (patientId, signal) =>
        apiService.getPatientMedications(patientId, signal),
      create: (data, signal) => apiService.createMedication(data, signal),
      update: (id, data, signal) =>
        apiService.updateMedication(id, data, signal),
      delete: (id, signal) => apiService.deleteMedication(id, signal),
    },
    requiresPatient: true,
  });

  // Get standardized configuration
  const config = getMedicalPageConfig('medications');

  // Use standardized data management
  const dataManagement = useDataManagement(medications, config);


  // Display medication purpose (indication only, since conditions are now linked via many-to-many)
  const getMedicationPurpose = (medication, asText = false) => {
    const indication = medication.indication?.trim();
    return indication || '-';
  };

  // Get standardized formatters for medications with linking support
  const formatters = {
    ...getEntityFormatters('medications', practitioners, navigate),
    // Override indication formatter to use smart display (text version for tables)
    indication: (value, medication) => getMedicationPurpose(medication, true),
  };


  // Form data state
  const [formData, setFormData] = useState({
    medication_name: '',
    dosage: '',
    frequency: '',
    route: '',
    indication: '',
    effective_period_start: '',
    effective_period_end: '',
    status: 'active',
    practitioner_id: null,
    pharmacy_id: null,
  });

  const handleInputChange = useCallback(e => {
    const { name, value } = e.target;
    let processedValue = value;

    // Handle ID fields - convert empty string to null, otherwise keep as string for Mantine
    if (name === 'practitioner_id' || name === 'pharmacy_id') {
      if (value === '') {
        processedValue = null;
      } else {
        processedValue = value; // Keep as string for Mantine compatibility
      }
    }

    setFormData(prev => ({
      ...prev,
      [name]: processedValue,
    }));
  }, []);

  const resetForm = useCallback(() => {
    setFormData({
      medication_name: '',
      dosage: '',
      frequency: '',
      route: '',
      indication: '',
      effective_period_start: '',
      effective_period_end: '',
      status: 'active',
      practitioner_id: null,
      pharmacy_id: null,
    });
    setEditingMedication(null);
    setShowAddForm(false);
  }, []);

  const handleAddMedication = () => {
    resetForm();
    setShowAddForm(true);
  };
  
  const handleCloseForm = useCallback(() => {
    setShowAddForm(false);
    setEditingMedication(null); // Clear editing state when closing
  }, []);

  const handleEditMedication = useCallback((medication) => {
    setFormData({
      medication_name: medication.medication_name || '',
      dosage: medication.dosage || '',
      frequency: medication.frequency || '',
      route: medication.route || '',
      indication: medication.indication || '',
      effective_period_start: medication.effective_period_start || '',
      effective_period_end: medication.effective_period_end || '',
      status: medication.status || 'active',
      practitioner_id: medication.practitioner_id ? String(medication.practitioner_id) : null,
      pharmacy_id: medication.pharmacy_id ? String(medication.pharmacy_id) : null,
    });
    setEditingMedication(medication);
    setShowAddForm(true);
  }, []);

  const handleViewMedication = medication => {
    setViewingMedication(medication);
    setShowViewModal(true);
    // Update URL with medication ID for sharing/bookmarking
    const searchParams = new URLSearchParams(location.search);
    searchParams.set('view', medication.id);
    navigate(`${location.pathname}?${searchParams.toString()}`, {
      replace: true,
    });
  };

  const handleCloseViewModal = () => {
    setShowViewModal(false);
    setViewingMedication(null);
    // Remove view parameter from URL
    const searchParams = new URLSearchParams(location.search);
    searchParams.delete('view');
    const newSearch = searchParams.toString();
    navigate(`${location.pathname}${newSearch ? `?${newSearch}` : ''}`, {
      replace: true,
    });
  };

  // Handle URL parameters for direct linking to specific medications
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const viewId = searchParams.get('view');

    if (viewId && medications.length > 0 && !loading) {
      const medication = medications.find(m => m.id.toString() === viewId);
      if (medication && !showViewModal) {
        // Only auto-open if modal isn't already open
        setViewingMedication(medication);
        setShowViewModal(true);
      }
    }
  }, [location.search, medications, loading, showViewModal]);


  const handleDeleteMedication = async medicationId => {
    const success = await deleteItem(medicationId);
    if (success) {
      await refreshData();
    }
  };

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    if (!currentPatient?.id) {
      setError('Patient information not available');
      return;
    }

    // Validate medication name
    const medicationName = formData.medication_name?.trim() || '';
    if (!medicationName) {
      setError('Medication name is required');
      return;
    }
    
    if (medicationName.length < 2) {
      setError('Medication name must be at least 2 characters long');
      return;
    }

    // Prepare medication data - ensure empty strings become null for optional fields
    const medicationData = {
      medication_name: medicationName,  // Required field, already trimmed
      dosage: formData.dosage?.trim() || null,
      frequency: formData.frequency?.trim() || null,
      route: formData.route?.trim() || null,
      indication: formData.indication?.trim() || null,
      status: formData.status || 'active',
      patient_id: currentPatient.id,
      practitioner_id: formData.practitioner_id
        ? parseInt(formData.practitioner_id)
        : null,
      pharmacy_id: formData.pharmacy_id ? parseInt(formData.pharmacy_id) : null,
    };

    // Add dates if provided
    if (formData.effective_period_start) {
      medicationData.effective_period_start = formData.effective_period_start;
    }
    if (formData.effective_period_end) {
      medicationData.effective_period_end = formData.effective_period_end;
    }

    // Log the data being sent for debugging
    logger.debug('Submitting medication data', {
      component: 'Medication',
      medicationData,
      formData
    });

    try {
      let success;
      if (editingMedication) {
        success = await updateItem(editingMedication.id, medicationData);
      } else {
        success = await createItem(medicationData);
      }

      if (success) {
        resetForm();
        await refreshData();
      }
    } catch (error) {
      logger.error('Error during save operation:', error);
    }
  }, [formData, currentPatient, editingMedication, setError, updateItem, createItem, resetForm, refreshData]);


  // Get processed data from data management and add practitioner/pharmacy names
  const processedMedications = useMemo(() => {
    return dataManagement.data.map(medication => ({
      ...medication,
      // Add practitioner name for sorting
      practitioner_name: medication.practitioner_id 
        ? practitioners.find(p => p.id === medication.practitioner_id)?.name || ''
        : '',
      // Add pharmacy name for sorting  
      pharmacy_name: medication.pharmacy_id
        ? pharmacies.find(p => p.id === medication.pharmacy_id)?.name || ''
        : ''
    }));
  }, [dataManagement.data, practitioners, pharmacies]);

  if (loading) {
    return (
      <Container size="xl" py="md" style={{ maxWidth: '100%', overflow: 'hidden' }}>
        <Center h={200}>
          <Stack align="center">
            <Loader size="lg" />
            <Text>Loading medications...</Text>
          </Stack>
        </Center>
      </Container>
    );
  }

  return (
    <Container size="xl" py="md" style={{ maxWidth: '100%', overflow: 'hidden' }}>
      <PageHeader title="Medications" icon="💊" />

      <Stack gap="lg">
        {error && (
          <Alert
            variant="light"
            color="red"
            title="Error"
            icon={<IconAlertTriangle size={16} />}
            withCloseButton
            onClose={clearError}
            mb="md"
          >
            {error}
          </Alert>
        )}

        {successMessage && (
          <Alert
            variant="light"
            color="green"
            title="Success"
            icon={<IconCheck size={16} />}
            mb="md"
          >
            {successMessage}
          </Alert>
        )}

        <Group justify="space-between" mb="lg">
          <Button
            variant="filled"
            leftSection={<IconPlus size={16} />}
            onClick={handleAddMedication}
            size="md"
          >
            Add New Medication
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

        {/* Form Modal */}
        <MedicationFormWrapper
          isOpen={showAddForm}
          onClose={handleCloseForm}
          title={editingMedication ? 'Edit Medication' : 'Add New Medication'}
          formData={formData}
          onInputChange={handleInputChange}
          onSubmit={handleSubmit}
          practitioners={practitioners}
          pharmacies={pharmacies}
          editingMedication={editingMedication}
        />

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {processedMedications.length === 0 ? (
            <Paper shadow="sm" p="xl" radius="md">
              <Center py="xl">
                <Stack align="center" gap="md">
                  <IconAlertTriangle
                    size={64}
                    stroke={1}
                    color="var(--mantine-color-gray-5)"
                  />
                  <Stack align="center" gap="xs">
                    <Title order={3}>No medications found</Title>
                    <Text c="dimmed" ta="center">
                      {dataManagement.hasActiveFilters
                        ? 'Try adjusting your search or filter criteria.'
                        : 'Click "Add New Medication" to get started.'}
                    </Text>
                  </Stack>
                </Stack>
              </Center>
            </Paper>
          ) : viewMode === 'cards' ? (
            <Grid>
              <AnimatePresence>
                {processedMedications.map((medication, index) => (
                  <Grid.Col
                    key={medication.id}
                    span={responsive.isMobile ? 12 : responsive.isTablet ? 6 : 4}
                  >
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                    >
                      <MedicationCard
                        medication={medication}
                        onView={handleViewMedication}
                        onEdit={handleEditMedication}
                        onDelete={handleDeleteMedication}
                        navigate={navigate}
                        onError={setError}
                      />
                    </motion.div>
                  </Grid.Col>
                ))}
              </AnimatePresence>
            </Grid>
          ) : (
            <Paper shadow="sm" radius="md" withBorder>
              <ResponsiveTable
                data={processedMedications}
                columns={[
                  { header: 'Medication Name', accessor: 'medication_name', priority: 'high', width: 200 },
                  { header: 'Dosage', accessor: 'dosage', priority: 'high', width: 120 },
                  { header: 'Frequency', accessor: 'frequency', priority: 'medium', width: 120 },
                  { header: 'Route', accessor: 'route', priority: 'low', width: 100 },
                  { header: 'Purpose', accessor: 'indication', priority: 'medium', width: 180 },
                  { header: 'Prescriber', accessor: 'practitioner_name', priority: 'low', width: 150 },
                  { header: 'Pharmacy', accessor: 'pharmacy_name', priority: 'low', width: 150 },
                  { header: 'Start Date', accessor: 'effective_period_start', priority: 'low', width: 120 },
                  { header: 'End Date', accessor: 'effective_period_end', priority: 'low', width: 120 },
                  { header: 'Status', accessor: 'status', priority: 'high', width: 100 },
                ]}
                patientData={currentPatient}
                tableName="Medications"
                onView={handleViewMedication}
                onEdit={handleEditMedication}
                onDelete={handleDeleteMedication}
                formatters={formatters}
                dataType="medical"
                responsive={responsive}
              />
            </Paper>
          )}
        </motion.div>

        {/* Medication View Modal */}
        <MedicationViewModal
          isOpen={showViewModal}
          onClose={handleCloseViewModal}
          medication={viewingMedication}
          onEdit={handleEditMedication}
          navigate={navigate}
          onError={setError}
        />
      </Stack>
    </Container>
  );
};

// Wrap with responsive HOC for enhanced responsive capabilities
export default withResponsive(Medication, {
  injectResponsive: true,
  displayName: 'ResponsiveMedication'
});
