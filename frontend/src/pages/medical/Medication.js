import React, { useState } from 'react';
import { useMedicalData } from '../../hooks/useMedicalData';
import { useDataManagement } from '../../hooks/useDataManagement';
import { apiService } from '../../services/api';
import { formatDate } from '../../utils/helpers';
import { getMedicalPageConfig } from '../../utils/medicalPageConfigs';
import { usePatientWithStaticData } from '../../hooks/useGlobalData';
import { PageHeader } from '../../components';
import { Button } from '../../components/ui';
import MantineFilters from '../../components/mantine/MantineFilters';
import MedicalTable from '../../components/shared/MedicalTable';
import ViewToggle from '../../components/shared/ViewToggle';
import MantineMedicalForm from '../../components/medical/MantineMedicalForm';
import StatusBadge from '../../components/medical/StatusBadge';
import {
  Badge,
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
} from '@mantine/core';

const Medication = () => {
  const [viewMode, setViewMode] = useState('cards');

  // Get practitioners and pharmacies data
  const { practitioners: practitionersObject, pharmacies: pharmaciesObject } =
    usePatientWithStaticData();

  const practitioners = practitionersObject?.practitioners || [];
  const pharmacies = pharmaciesObject?.pharmacies || [];

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

  // Form and UI state
  const [showModal, setShowModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingMedication, setViewingMedication] = useState(null);
  const [editingMedication, setEditingMedication] = useState(null);
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

  const handleAddMedication = () => {
    setEditingMedication(null);
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
    setShowModal(true);
  };

  const handleEditMedication = medication => {
    setEditingMedication(medication);
    setFormData({
      medication_name: medication.medication_name || '',
      dosage: medication.dosage || '',
      frequency: medication.frequency || '',
      route: medication.route || '',
      indication: medication.indication || '',
      effective_period_start: medication.effective_period_start || '',
      effective_period_end: medication.effective_period_end || '',
      status: medication.status || 'active',
      practitioner_id: medication.practitioner_id || null,
      pharmacy_id: medication.pharmacy_id || null,
    });
    setShowModal(true);
  };

  const handleViewMedication = medication => {
    setViewingMedication(medication);
    setShowViewModal(true);
  };

  const handleDeleteMedication = async medicationId => {
    const success = await deleteItem(medicationId);
    if (success) {
      await refreshData();
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!currentPatient?.id) {
      setError('Patient information not available');
      return;
    }

    const medicationData = {
      medication_name: formData.medication_name?.trim() || '',
      dosage: formData.dosage?.trim() || '',
      frequency: formData.frequency?.trim() || '',
      route: formData.route?.trim() || '',
      indication: formData.indication?.trim() || '',
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

    let success;
    if (editingMedication) {
      success = await updateItem(editingMedication.id, medicationData);
    } else {
      success = await createItem(medicationData);
    }

    if (success) {
      setShowModal(false);
      await refreshData();
    }
  };

  const handleInputChange = e => {
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
  };

  // Get processed data from data management
  const filteredMedications = dataManagement.data;

  if (loading) {
    return (
      <Container size="xl" py="xl">
        <Center h={200}>
          <Stack align="center">
            <Loader size="lg" />
            <Text>Loading medications...</Text>
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
        <PageHeader title="Medications" icon="💊" />

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
          {successMessage && (
            <Alert variant="light" color="green" title="Success">
              {successMessage}
            </Alert>
          )}

          <Group justify="space-between" align="center">
            <Button variant="filled" onClick={handleAddMedication}>
              + Add New Medication
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

          {filteredMedications.length === 0 ? (
            <Card withBorder p="xl">
              <Stack align="center" gap="md">
                <Text size="3rem">💊</Text>
                <Text size="xl" fw={600}>
                  No Medications Found
                </Text>
                <Text ta="center" c="dimmed">
                  {dataManagement.hasActiveFilters
                    ? 'Try adjusting your search or filter criteria.'
                    : 'Start by adding your first medication.'}
                </Text>
                {!dataManagement.hasActiveFilters && (
                  <Button variant="filled" onClick={handleAddMedication}>
                    Add Your First Medication
                  </Button>
                )}
              </Stack>
            </Card>
          ) : viewMode === 'cards' ? (
            <Grid>
              {filteredMedications.map(medication => (
                <Grid.Col key={medication.id} span={{ base: 12, sm: 6, lg: 4 }}>
                  <Card
                    withBorder
                    shadow="sm"
                    radius="md"
                    h="100%"
                    style={{ display: 'flex', flexDirection: 'column' }}
                  >
                    <Stack gap="sm" style={{ flex: 1 }}>
                      <Group justify="space-between" align="flex-start">
                        <Stack gap="xs" style={{ flex: 1 }}>
                          <Text fw={600} size="lg">
                            {medication.medication_name}
                          </Text>
                          {medication.dosage && (
                            <Badge variant="light" color="blue" size="md">
                              {medication.dosage}
                            </Badge>
                          )}
                        </Stack>
                        <StatusBadge status={medication.status} />
                      </Group>

                      <Stack gap="xs">
                        {medication.frequency && (
                          <Group>
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              Frequency:
                            </Text>
                            <Text size="sm">{medication.frequency}</Text>
                          </Group>
                        )}
                        {medication.route && (
                          <Group>
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              Route:
                            </Text>
                            <Badge variant="light" color="cyan" size="sm">
                              {medication.route}
                            </Badge>
                          </Group>
                        )}
                        {medication.indication && (
                          <Group align="flex-start">
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              Indication:
                            </Text>
                            <Text size="sm" style={{ flex: 1 }}>
                              {medication.indication}
                            </Text>
                          </Group>
                        )}
                        {medication.practitioner && (
                          <Group>
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              Prescriber:
                            </Text>
                            <Text size="sm">
                              {medication.practitioner.name}
                            </Text>
                          </Group>
                        )}
                        {medication.pharmacy && (
                          <Group>
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              Pharmacy:
                            </Text>
                            <Text size="sm">{medication.pharmacy.name}</Text>
                          </Group>
                        )}
                        {medication.effective_period_start && (
                          <Group>
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              Start Date:
                            </Text>
                            <Text size="sm">
                              {formatDate(medication.effective_period_start)}
                            </Text>
                          </Group>
                        )}
                        {medication.effective_period_end && (
                          <Group>
                            <Text size="sm" fw={500} c="dimmed" w={120}>
                              End Date:
                            </Text>
                            <Text size="sm">
                              {formatDate(medication.effective_period_end)}
                            </Text>
                          </Group>
                        )}
                      </Stack>
                    </Stack>

                    {/* Buttons always at bottom */}
                    <Stack gap={0} mt="auto">
                      <Divider />
                      <Group justify="flex-end" gap="xs" pt="sm">
                        <Button
                          variant="light"
                          size="xs"
                          onClick={() => handleViewMedication(medication)}
                        >
                          View
                        </Button>
                        <Button
                          variant="light"
                          size="xs"
                          onClick={() => handleEditMedication(medication)}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="light"
                          color="red"
                          size="xs"
                          onClick={() => handleDeleteMedication(medication.id)}
                        >
                          Delete
                        </Button>
                      </Group>
                    </Stack>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          ) : (
            <MedicalTable
              data={filteredMedications}
              columns={[
                { header: 'Medication Name', accessor: 'medication_name' },
                { header: 'Dosage', accessor: 'dosage' },
                { header: 'Frequency', accessor: 'frequency' },
                { header: 'Route', accessor: 'route' },
                { header: 'Indication', accessor: 'indication' },
                { header: 'Prescriber', accessor: 'practitioner_name' },
                { header: 'Pharmacy', accessor: 'pharmacy_name' },
                { header: 'Start Date', accessor: 'effective_period_start' },
                { header: 'End Date', accessor: 'effective_period_end' },
                { header: 'Status', accessor: 'status' },
              ]}
              patientData={currentPatient}
              tableName="Medications"
              onView={handleViewMedication}
              onEdit={handleEditMedication}
              onDelete={handleDeleteMedication}
              formatters={{
                medication_name: value => (
                  <Text fw={600} style={{ minWidth: 150 }}>
                    {value}
                  </Text>
                ),
                dosage: value =>
                  value ? (
                    <Badge variant="filled" color="blue" size="sm">
                      {value}
                    </Badge>
                  ) : (
                    '-'
                  ),
                frequency: value => value || '-',
                route: value =>
                  value ? (
                    <Badge variant="light" color="cyan" size="sm">
                      {value}
                    </Badge>
                  ) : (
                    '-'
                  ),
                indication: value =>
                  value ? (
                    <span title={value}>
                      {value.length > 50
                        ? `${value.substring(0, 50)}...`
                        : value}
                    </span>
                  ) : (
                    '-'
                  ),
                effective_period_start: value =>
                  value ? formatDate(value) : '-',
                effective_period_end: value =>
                  value ? formatDate(value) : '-',
                status: value => <StatusBadge status={value} size="small" />,
                practitioner_name: (value, item) =>
                  item.practitioner?.name || '-',
                pharmacy_name: (value, item) => item.pharmacy?.name || '-',
              }}
            />
          )}
        </Stack>
      </Container>

      <MantineMedicalForm
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingMedication ? 'Edit Medication' : 'Add New Medication'}
        formData={formData}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
        practitioners={practitioners}
        pharmacies={pharmacies}
        editingMedication={editingMedication}
      />

      {/* Medication View Modal */}
      <Modal
        opened={showViewModal}
        onClose={() => setShowViewModal(false)}
        title={
          <Group>
            <Text size="lg" fw={600}>
              Medication Details
            </Text>
            {viewingMedication && (
              <StatusBadge status={viewingMedication.status} />
            )}
          </Group>
        }
        size="lg"
        centered
      >
        {viewingMedication && (
          <Stack gap="md">
            <Card withBorder p="md">
              <Stack gap="sm">
                <Group justify="space-between" align="flex-start">
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Title order={3}>{viewingMedication.medication_name}</Title>
                    {viewingMedication.dosage && (
                      <Badge variant="light" color="blue" size="lg">
                        {viewingMedication.dosage}
                      </Badge>
                    )}
                  </Stack>
                </Group>

                {viewingMedication.indication && (
                  <Stack gap="xs">
                    <Text fw={500} c="dimmed" size="sm">
                      Indication
                    </Text>
                    <Text>{viewingMedication.indication}</Text>
                  </Stack>
                )}
              </Stack>
            </Card>

            <Grid>
              <Grid.Col span={6}>
                <Card withBorder p="md" h="100%">
                  <Stack gap="sm">
                    <Text fw={600} size="sm" c="dimmed">
                      DOSAGE & FREQUENCY
                    </Text>
                    <Divider />
                    {viewingMedication.dosage && (
                      <Group>
                        <Text size="sm" fw={500} w={80}>
                          Dosage:
                        </Text>
                        <Text size="sm">{viewingMedication.dosage}</Text>
                      </Group>
                    )}
                    {viewingMedication.frequency && (
                      <Group>
                        <Text size="sm" fw={500} w={80}>
                          Frequency:
                        </Text>
                        <Text size="sm">{viewingMedication.frequency}</Text>
                      </Group>
                    )}
                    {viewingMedication.route && (
                      <Group>
                        <Text size="sm" fw={500} w={80}>
                          Route:
                        </Text>
                        <Badge variant="light" color="cyan" size="sm">
                          {viewingMedication.route}
                        </Badge>
                      </Group>
                    )}
                    {!viewingMedication.dosage &&
                      !viewingMedication.frequency &&
                      !viewingMedication.route && (
                        <Text size="sm" c="dimmed">
                          No dosage information
                        </Text>
                      )}
                  </Stack>
                </Card>
              </Grid.Col>

              <Grid.Col span={6}>
                <Card withBorder p="md" h="100%">
                  <Stack gap="sm">
                    <Text fw={600} size="sm" c="dimmed">
                      PRESCRIBER & PHARMACY
                    </Text>
                    <Divider />
                    {viewingMedication.practitioner && (
                      <Group>
                        <Text size="sm" fw={500} w={80}>
                          Prescriber:
                        </Text>
                        <Text size="sm">
                          {viewingMedication.practitioner.name}
                        </Text>
                      </Group>
                    )}
                    {viewingMedication.pharmacy && (
                      <Group>
                        <Text size="sm" fw={500} w={80}>
                          Pharmacy:
                        </Text>
                        <Text size="sm">{viewingMedication.pharmacy.name}</Text>
                      </Group>
                    )}
                    {!viewingMedication.practitioner &&
                      !viewingMedication.pharmacy && (
                        <Text size="sm" c="dimmed">
                          No prescriber or pharmacy information
                        </Text>
                      )}
                  </Stack>
                </Card>
              </Grid.Col>
            </Grid>

            {(viewingMedication.effective_period_start ||
              viewingMedication.effective_period_end) && (
              <Card withBorder p="md">
                <Stack gap="sm">
                  <Text fw={600} size="sm" c="dimmed">
                    EFFECTIVE PERIOD
                  </Text>
                  <Divider />
                  <Grid>
                    {viewingMedication.effective_period_start && (
                      <Grid.Col span={6}>
                        <Group>
                          <Text size="sm" fw={500} w={80}>
                            Start Date:
                          </Text>
                          <Text size="sm">
                            {formatDate(
                              viewingMedication.effective_period_start
                            )}
                          </Text>
                        </Group>
                      </Grid.Col>
                    )}
                    {viewingMedication.effective_period_end && (
                      <Grid.Col span={6}>
                        <Group>
                          <Text size="sm" fw={500} w={80}>
                            End Date:
                          </Text>
                          <Text size="sm">
                            {formatDate(viewingMedication.effective_period_end)}
                          </Text>
                        </Group>
                      </Grid.Col>
                    )}
                  </Grid>
                </Stack>
              </Card>
            )}

            <Group justify="flex-end" mt="md">
              <Button
                variant="light"
                onClick={() => {
                  setShowViewModal(false);
                  handleEditMedication(viewingMedication);
                }}
              >
                Edit Medication
              </Button>
              <Button variant="filled" onClick={() => setShowViewModal(false)}>
                Close
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </>
  );
};

export default Medication;
