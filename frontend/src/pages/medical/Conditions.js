import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Container,
  Paper,
  Group,
  Text,
  Title,
  Stack,
  Alert,
  Loader,
  Center,
  Badge,
  Grid,
  Card,
  Box,
  Divider,
  Modal,
  Button,
} from '@mantine/core';
import {
  IconAlertTriangle,
  IconCheck,
  IconPlus,
  IconShieldCheck,
  IconHeart,
  IconBrain,
  IconLungs,
  IconBone,
  IconDroplet,
  IconAward,
} from '@tabler/icons-react';
import { useMedicalData, useDataManagement } from '../../hooks';
import { apiService } from '../../services/api';
import { formatDate } from '../../utils/helpers';
import { getMedicalPageConfig } from '../../utils/medicalPageConfigs';
import { getEntityFormatters } from '../../utils/tableFormatters';
import { PageHeader } from '../../components';
import MantineFilters from '../../components/mantine/MantineFilters';
import MedicalTable from '../../components/shared/MedicalTable';
import ViewToggle from '../../components/shared/ViewToggle';

// Modular components
import {
  ConditionCard,
  ConditionViewModal,
} from '../../components/medical/conditions';
import MantineConditionForm from '../../components/medical/MantineConditionForm';

const Conditions = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  
  // Load medications and practitioners for linking dropdowns
  const [medications, setMedications] = useState([]);
  const [practitioners, setPractitioners] = useState([]);
  

  // Standardized data management
  const {
    items: conditions,
    currentPatient,
    loading,
    error,
    successMessage,
    createItem,
    updateItem,
    deleteItem,
    refreshData,
    clearError,
    setSuccessMessage,
    setError,
  } = useMedicalData({
    entityName: 'condition',
    apiMethodsConfig: {
      getAll: signal => apiService.getConditions(signal),
      getByPatient: (patientId, signal) =>
        apiService.getPatientConditions(patientId, signal),
      create: (data, signal) => apiService.createCondition(data, signal),
      update: (id, data, signal) =>
        apiService.updateCondition(id, data, signal),
      delete: (id, signal) => apiService.deleteCondition(id, signal),
    },
    requiresPatient: true,
  });

  // Standardized filtering and sorting using configuration
  const config = getMedicalPageConfig('conditions');
  const dataManagement = useDataManagement(conditions, config);

  // Form and UI state
  const [showModal, setShowModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingCondition, setViewingCondition] = useState(null);
  const [editingCondition, setEditingCondition] = useState(null);
  const [formData, setFormData] = useState({
    condition_name: '',
    diagnosis: '',
    notes: '',
    status: 'active',
    severity: '',
    medication_id: '',
    practitioner_id: '',
    icd10_code: '',
    snomed_code: '',
    code_description: '',
    onset_date: '', // Form field name
    end_date: '', // Form field name
  });

  const handleAddCondition = () => {
    setEditingCondition(null);
    setFormData({
      condition_name: '',
      diagnosis: '',
      notes: '',
      status: 'active',
      severity: '',
      medication_id: '',
      practitioner_id: '',
      icd10_code: '',
      snomed_code: '',
      code_description: '',
      onset_date: '',
      end_date: '',
    });
    setShowModal(true);
  };

  const handleViewCondition = condition => {
    setViewingCondition(condition);
    setShowViewModal(true);
    // Update URL with condition ID for sharing/bookmarking
    const searchParams = new URLSearchParams(location.search);
    searchParams.set('view', condition.id);
    navigate(`${location.pathname}?${searchParams.toString()}`, {
      replace: true,
    });
  };

  const handleCloseViewModal = () => {
    setShowViewModal(false);
    setViewingCondition(null);
    // Remove view parameter from URL
    const searchParams = new URLSearchParams(location.search);
    searchParams.delete('view');
    const newSearch = searchParams.toString();
    navigate(`${location.pathname}${newSearch ? `?${newSearch}` : ''}`, {
      replace: true,
    });
  };

  // Load medications and practitioners for linking dropdowns
  useEffect(() => {
    if (currentPatient?.id) {
      // Load medications
      apiService.getPatientMedications(currentPatient.id)
        .then(response => {
          setMedications(response || []);
        })
        .catch(error => {
          console.error('Failed to fetch medications:', error);
          setMedications([]);
        });
      
      // Load practitioners
      apiService.getPractitioners()
        .then(response => {
          setPractitioners(response || []);
        })
        .catch(error => {
          console.error('Failed to fetch practitioners:', error);
          setPractitioners([]);
        });
    }
  }, [currentPatient?.id]);

  // Handle URL parameters for direct linking to specific conditions
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const viewId = searchParams.get('view');

    if (viewId && conditions.length > 0 && !loading) {
      const condition = conditions.find(c => c.id.toString() === viewId);
      if (condition && !showViewModal) {
        // Only auto-open if modal isn't already open
        setViewingCondition(condition);
        setShowViewModal(true);
      }
    }
  }, [location.search, conditions, loading, showViewModal]);

  const handleEditCondition = condition => {
    setEditingCondition(condition);
    setFormData({
      condition_name: condition.condition_name || '',
      diagnosis: condition.diagnosis || '',
      notes: condition.notes || '',
      status: condition.status || 'active',
      severity: condition.severity || '',
      medication_id: condition.medication_id ? condition.medication_id.toString() : '',
      practitioner_id: condition.practitioner_id ? condition.practitioner_id.toString() : '',
      icd10_code: condition.icd10_code || '',
      snomed_code: condition.snomed_code || '',
      code_description: condition.code_description || '',
      onset_date: condition.onset_date
        ? condition.onset_date.split('T')[0]
        : '',
      end_date: condition.end_date ? condition.end_date.split('T')[0] : '',
    });
    setShowModal(true);
  };

  const handleDeleteCondition = async conditionId => {
    const success = await deleteItem(conditionId);
    if (success) {
      await refreshData();
    }
  };

  const handleMedicationClick = (medicationId) => {
    navigate(`/medications?view=${medicationId}`);
  };

  const handlePractitionerClick = (practitionerId) => {
    navigate(`/practitioners?view=${practitionerId}`);
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!currentPatient?.id) {
      setError('Patient information not available');
      return;
    }

    const conditionData = {
      condition_name: formData.condition_name || null,
      diagnosis: formData.diagnosis,
      notes: formData.notes || null,
      status: formData.status,
      severity: formData.severity || null,
      medication_id: formData.medication_id ? parseInt(formData.medication_id) : null,
      practitioner_id: formData.practitioner_id ? parseInt(formData.practitioner_id) : null,
      icd10_code: formData.icd10_code || null,
      snomed_code: formData.snomed_code || null,
      code_description: formData.code_description || null,
      onset_date: formData.onset_date || null, // Use snake_case to match API
      end_date: formData.end_date || null, // Use snake_case to match API
      patient_id: currentPatient.id,
    };

    let success;
    if (editingCondition) {
      success = await updateItem(editingCondition.id, conditionData);
    } else {
      success = await createItem(conditionData);
    }

    if (success) {
      setShowModal(false);
      await refreshData();
    }
  };

  const handleInputChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const filteredConditions = dataManagement.data;


  if (loading) {
    return (
      <Container size="xl" py="lg">
        <Center py="xl">
          <Stack align="center" gap="md">
            <Loader size="lg" />
            <Text size="lg">Loading conditions...</Text>
          </Stack>
        </Center>
      </Container>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <PageHeader title="Medical Conditions" icon="🏥" />

      <Container size="xl" py="lg">
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
            onClick={handleAddCondition}
            size="md"
          >
            Add New Condition
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
        <MantineConditionForm
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title={editingCondition ? 'Edit Condition' : 'Add New Condition'}
          formData={formData}
          onInputChange={handleInputChange}
          onSubmit={handleSubmit}
          editingCondition={editingCondition}
          medications={medications}
          navigate={navigate}
        />

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          {filteredConditions.length === 0 ? (
            <Paper shadow="sm" p="xl" radius="md">
              <Center py="xl">
                <Stack align="center" gap="md">
                  <IconShieldCheck
                    size={64}
                    stroke={1}
                    color="var(--mantine-color-gray-5)"
                  />
                  <Stack align="center" gap="xs">
                    <Title order={3}>No medical conditions found</Title>
                    <Text c="dimmed" ta="center">
                      {dataManagement.hasActiveFilters
                        ? 'Try adjusting your search or filter criteria.'
                        : 'Click "Add New Condition" to get started.'}
                    </Text>
                  </Stack>
                </Stack>
              </Center>
            </Paper>
          ) : viewMode === 'cards' ? (
            <Grid>
              <AnimatePresence>
                {filteredConditions.map((condition, index) => (
                  <Grid.Col
                    key={condition.id}
                    span={{ base: 12, md: 6, lg: 4 }}
                  >
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                    >
                      <ConditionCard
                        condition={condition}
                        onView={handleViewCondition}
                        onEdit={handleEditCondition}
                        onDelete={handleDeleteCondition}
                        navigate={navigate}
                      />
                    </motion.div>
                  </Grid.Col>
                ))}
              </AnimatePresence>
            </Grid>
          ) : (
            <Paper shadow="sm" radius="md" withBorder>
              <MedicalTable
                data={filteredConditions}
                columns={[
                  { header: 'Condition', accessor: 'diagnosis' },
                  { header: 'Severity', accessor: 'severity' },
                  { header: 'Onset Date', accessor: 'onset_date' },
                  { header: 'End Date', accessor: 'end_date' },
                  { header: 'Status', accessor: 'status' },
                  { header: 'ICD-10', accessor: 'icd10_code' },
                  { header: 'Notes', accessor: 'notes' },
                ]}
                patientData={currentPatient}
                tableName="Conditions"
                onView={handleViewCondition}
                onEdit={handleEditCondition}
                onDelete={handleDeleteCondition}
                formatters={{
                  diagnosis: getEntityFormatters('conditions').condition_name,
                  severity: getEntityFormatters('conditions').severity,
                  onset_date: getEntityFormatters('conditions').onset_date,
                  end_date: getEntityFormatters('conditions').end_date,
                  status: getEntityFormatters('conditions').status,
                  icd10_code: getEntityFormatters('conditions').simple,
                  notes: getEntityFormatters('conditions').notes,
                }}
              />
            </Paper>
          )}
        </motion.div>

        {/* Condition View Modal */}
        <ConditionViewModal
          isOpen={showViewModal}
          onClose={handleCloseViewModal}
          condition={viewingCondition}
          onEdit={handleEditCondition}
          medications={medications}
          practitioners={practitioners}
          onMedicationClick={handleMedicationClick}
          onPractitionerClick={handlePractitionerClick}
        />
      </Container>
    </motion.div>
  );
};

export default Conditions;
