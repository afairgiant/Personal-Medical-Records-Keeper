import React from 'react';
import { Divider, Stack, Title, Paper, Text, Badge } from '@mantine/core';
import BaseMedicalForm from './BaseMedicalForm';
import ConditionRelationships from './ConditionRelationships';
import { labResultFormFields } from '../../utils/medicalFormFields';

const MantineLabResultForm = ({
  isOpen,
  onClose,
  title,
  formData,
  onInputChange,
  onSubmit,
  practitioners = [],
  editingLabResult = null,
  children, // For file management section in edit mode
  // Condition relationship props
  conditions = [],
  labResultConditions = {},
  fetchLabResultConditions,
  navigate,
  currentPatient,
}) => {
  // Status options with visual indicators
  const statusOptions = [
    { value: 'ordered', label: 'Ordered - Test has been requested' },
    { value: 'in-progress', label: 'In Progress - Sample being processed' },
    { value: 'completed', label: 'Completed - Results available' },
    { value: 'cancelled', label: 'Cancelled - Test was cancelled' },
  ];

  // Test category options
  const categoryOptions = [
    { value: 'blood work', label: 'Blood Work' },
    { value: 'imaging', label: 'Imaging (X-ray, MRI, CT)' },
    { value: 'pathology', label: 'Pathology' },
    { value: 'microbiology', label: 'Microbiology' },
    { value: 'chemistry', label: 'Chemistry' },
    { value: 'hematology', label: 'Hematology' },
    { value: 'immunology', label: 'Immunology' },
    { value: 'genetics', label: 'Genetics' },
    { value: 'cardiology', label: 'Cardiology' },
    { value: 'pulmonology', label: 'Pulmonology' },
    { value: 'other', label: 'Other' },
  ];

  // Test type options with urgency levels
  const testTypeOptions = [
    { value: 'routine', label: 'Routine - Standard processing' },
    { value: 'urgent', label: 'Urgent - Expedited processing' },
    { value: 'emergency', label: 'Emergency - Critical priority' },
    { value: 'follow-up', label: 'Follow-up - Repeat testing' },
    { value: 'screening', label: 'Screening - Preventive testing' },
  ];

  // Lab result options with color coding
  const labResultOptions = [
    {
      value: 'normal',
      label: 'Normal - Within reference range',
      color: 'green',
    },
    {
      value: 'abnormal',
      label: 'Abnormal - Outside reference range',
      color: 'red',
    },
    {
      value: 'critical',
      label: 'Critical - Requires immediate attention',
      color: 'red',
    },
    { value: 'high', label: 'High - Above normal range', color: 'orange' },
    { value: 'low', label: 'Low - Below normal range', color: 'orange' },
    {
      value: 'borderline',
      label: 'Borderline - Near threshold',
      color: 'yellow',
    },
    {
      value: 'inconclusive',
      label: 'Inconclusive - Needs repeat',
      color: 'gray',
    },
  ];

  // Convert practitioners to Mantine format
  const practitionerOptions = practitioners.map(practitioner => ({
    value: String(practitioner.id),
    label: `${practitioner.name} - ${practitioner.specialty}`,
  }));

  const dynamicOptions = {
    categories: categoryOptions,
    testTypes: testTypeOptions,
    practitioners: practitionerOptions,
    statuses: statusOptions,
    results: labResultOptions,
  };

  // Get status color
  const getStatusColor = status => {
    switch (status) {
      case 'ordered':
        return 'blue';
      case 'in-progress':
        return 'yellow';
      case 'completed':
        return 'green';
      case 'cancelled':
        return 'red';
      default:
        return 'gray';
    }
  };

  // Get result badge
  const getResultBadge = result => {
    const option = labResultOptions.find(opt => opt.value === result);
    if (!option) return null;
    return (
      <Badge color={option.color} variant="light" size="sm">
        {option.value.charAt(0).toUpperCase() + option.value.slice(1)}
      </Badge>
    );
  };

  // Custom content for divider, badges, condition relationships, and file management
  const customContent = (
    <>
      <Divider label="Test Details" labelPosition="center" />
      
      {/* Status Badge */}
      {formData.status && (
        <div style={{ marginTop: '-8px', marginBottom: '8px' }}>
          <Text size="sm" fw={500} mb="xs">Status Indicator:</Text>
          <Badge
            color={getStatusColor(formData.status)}
            variant="light"
            size="sm"
          >
            {formData.status.charAt(0).toUpperCase() + formData.status.slice(1)}
          </Badge>
        </div>
      )}

      {/* Result Badge */}
      {formData.labs_result && (
        <div style={{ marginBottom: '16px' }}>
          <Text size="sm" fw={500} mb="xs">Result Indicator:</Text>
          {getResultBadge(formData.labs_result)}
        </div>
      )}

      {/* Condition Relationships Section for Edit Mode */}
      {editingLabResult && conditions.length > 0 && (
        <>
          <Divider label="Related Conditions" labelPosition="center" mt="lg" />
          <Paper withBorder p="md" bg="gray.1">
            <Stack gap="md">
              <Title order={5}>Link Medical Conditions</Title>
              <Text size="sm" c="dimmed">
                Associate this lab result with relevant medical conditions for better tracking and organization.
              </Text>
              <ConditionRelationships 
                labResultId={editingLabResult.id}
                labResultConditions={labResultConditions}
                conditions={conditions}
                fetchLabResultConditions={fetchLabResultConditions}
                navigate={navigate}
                currentPatient={currentPatient}
              />
            </Stack>
          </Paper>
        </>
      )}

      {/* File Management Section (passed as children for edit mode) */}
      {children}
    </>
  );

  return (
    <BaseMedicalForm
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      formData={formData}
      onInputChange={onInputChange}
      onSubmit={onSubmit}
      editingItem={editingLabResult}
      fields={labResultFormFields}
      dynamicOptions={dynamicOptions}
      modalSize="xl"
    >
      {customContent}
    </BaseMedicalForm>
  );
};

export default MantineLabResultForm;
