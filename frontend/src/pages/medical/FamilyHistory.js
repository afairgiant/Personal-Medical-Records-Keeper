import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMedicalData } from '../../hooks/useMedicalData';
import { useDataManagement } from '../../hooks/useDataManagement';
import { apiService } from '../../services/api';
import { formatDate } from '../../utils/helpers';
import { getMedicalPageConfig } from '../../utils/medicalPageConfigs';
import { usePatientWithStaticData } from '../../hooks/useGlobalData';
import { getEntityFormatters } from '../../utils/tableFormatters';
import { navigateToEntity } from '../../utils/linkNavigation';
import { useFormErrorHandling } from '../../hooks/useFormErrorHandling';
import { PageHeader } from '../../components';
import { Button } from '../../components/ui';
import logger from '../../services/logger';
import MantineFilters from '../../components/mantine/MantineFilters';
import MedicalTable from '../../components/shared/MedicalTable';
import ViewToggle from '../../components/shared/ViewToggle';
import MantineFamilyMemberForm from '../../components/medical/MantineFamilyMemberForm';
import MantineFamilyConditionForm from '../../components/medical/MantineFamilyConditionForm';
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
  ActionIcon,
  Collapse,
  Box,
  SimpleGrid,
} from '@mantine/core';
import {
  IconUsers,
  IconPlus,
  IconEdit,
  IconTrash,
  IconChevronDown,
  IconChevronUp,
  IconMedicalCross,
  IconUserPlus,
  IconStethoscope,
} from '@tabler/icons-react';

const FamilyHistory = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [viewMode, setViewMode] = useState('cards');
  const [expandedMembers, setExpandedMembers] = useState(new Set());

  // Modern data management with useMedicalData
  const {
    items: familyMembers,
    currentPatient,
    loading,
    error,
    lastErrorObject,
    successMessage,
    createItem,
    updateItem,
    deleteItem,
    refreshData,
    clearError,
    setError,
  } = useMedicalData({
    entityName: 'family_member',
    apiMethodsConfig: {
      getAll: signal => {
        logger.debug('Getting all family members', {
          component: 'FamilyHistory',
        });
        return apiService.getFamilyMembers(signal);
      },
      getByPatient: (patientId, signal) => {
        logger.debug('Getting family members for patient', {
          patientId,
          component: 'FamilyHistory',
        });
        return apiService.getPatientFamilyMembers(patientId, signal);
      },
      create: (data, signal) => {
        logger.debug('Creating family member', {
          data,
          component: 'FamilyHistory',
        });
        return apiService.createFamilyMember(data, signal);
      },
      update: (id, data, signal) => {
        logger.debug('Updating family member', {
          id,
          data,
          component: 'FamilyHistory',
        });
        return apiService.updateFamilyMember(id, data, signal);
      },
      delete: (id, signal) => {
        logger.debug('Deleting family member', {
          id,
          component: 'FamilyHistory',
        });
        return apiService.deleteFamilyMember(id, signal);
      },
    },
    requiresPatient: true,
  });

  // Extract family member ID from URL for view modal
  const urlParams = new URLSearchParams(location.search);
  const viewingFamilyMemberId = urlParams.get('view');
  const viewingFamilyMember = familyMembers.find(
    m => m.id === parseInt(viewingFamilyMemberId)
  );

  // Get standardized configuration
  const config = getMedicalPageConfig('family_members');

  // Use standardized data management for filtering and sorting
  const dataManagement = useDataManagement(familyMembers, config);

  // Form and UI state
  const [showModal, setShowModal] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    relationship: '',
    gender: '',
    birth_year: '',
    death_year: '',
    is_deceased: false,
    notes: '',
  });
  
  // Enhanced error handling
  const { 
    fieldErrors, 
    clearFieldErrors, 
    handleSubmissionError, 
    createChangeHandler 
  } = useFormErrorHandling('FamilyHistory');

  // Family condition state
  const [showConditionModal, setShowConditionModal] = useState(false);
  const [editingCondition, setEditingCondition] = useState(null);
  const [selectedFamilyMember, setSelectedFamilyMember] = useState(null);
  const [selectedFamilyMemberId, setSelectedFamilyMemberId] = useState(null);
  const [openedFromViewModal, setOpenedFromViewModal] = useState(false);
  const [conditionFormData, setConditionFormData] = useState({
    condition_name: '',
    condition_type: '',
    severity: '',
    diagnosis_age: '',
    notes: '',
  });

  const handleInputChange = createChangeHandler((e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  });

  const handleConditionInputChange = e => {
    const { name, value, type, checked } = e.target;
    setConditionFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      relationship: '',
      gender: '',
      birth_year: '',
      death_year: '',
      is_deceased: false,
      notes: '',
    });
    clearFieldErrors();
    setEditingMember(null);
    setShowModal(false);
  };

  const resetConditionForm = () => {
    setConditionFormData({
      condition_name: '',
      condition_type: '',
      severity: '',
      diagnosis_age: '',
      notes: '',
    });
    setEditingCondition(null);
    // Don't reset selectedFamilyMember here since we need it for form submission
    // setSelectedFamilyMember(null);
    setShowConditionModal(false);
  };

  const handleAddMember = () => {
    resetForm();
    setShowModal(true);
  };

  const handleEditMember = member => {
    setEditingMember(member);
    setFormData({
      name: member.name || '',
      relationship: member.relationship || '',
      gender: member.gender || '',
      birth_year: member.birth_year || '',
      death_year: member.death_year || '',
      is_deceased: member.is_deceased || false,
      notes: member.notes || '',
    });
    setShowModal(true);
  };

  const handleDeleteMember = async memberId => {
    if (
      !window.confirm('Are you sure you want to delete this family member?')
    ) {
      return;
    }

    try {
      await deleteItem(memberId);
    } catch (error) {
      console.error('Failed to delete family member:', error);
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();
    
    // Clear previous errors
    clearFieldErrors();
    clearError();

    if (!currentPatient?.id) {
      setError('Patient information not available');
      return;
    }

    logger.debug('Submitting family member data', {
      formData,
      patientId: currentPatient.id,
      component: 'FamilyHistory',
    });

    const memberData = {
      name: formData.name,
      relationship: formData.relationship,
      gender: formData.gender || null,
      birth_year: formData.birth_year || null,
      death_year: formData.death_year || null,
      is_deceased: formData.is_deceased,
      notes: formData.notes || null,
      patient_id: currentPatient.id,
    };

    let success;
    if (editingMember) {
      success = await updateItem(editingMember.id, memberData);
    } else {
      success = await createItem(memberData);
    }

    if (success) {
      logger.debug('Family member submission successful', {
        action: editingMember ? 'update' : 'create',
        familyMemberId: editingMember?.id,
        component: 'FamilyHistory',
      });
      setShowModal(false);
      await refreshData();
    } else {
      // Use centralized error handling
      const errorToHandle = lastErrorObject || { message: error };
      handleSubmissionError(errorToHandle, memberData, setError);
    }
  };

  const handleCancel = () => {
    resetForm();
  };

  const handleAddCondition = familyMember => {
    logger.debug('Adding condition for family member', {
      familyMember: familyMember.name,
      familyMemberId: familyMember.id,
      component: 'FamilyHistory',
    });
    setSelectedFamilyMember(familyMember);
    setSelectedFamilyMemberId(familyMember.id);
    setOpenedFromViewModal(false);
    resetConditionForm();
    setShowConditionModal(true);
  };

  const handleEditCondition = (familyMember, condition) => {
    setSelectedFamilyMember(familyMember);
    setSelectedFamilyMemberId(familyMember.id);
    setOpenedFromViewModal(false);
    setEditingCondition(condition);
    setConditionFormData({
      condition_name: condition.condition_name || '',
      condition_type: condition.condition_type || '',
      severity: condition.severity || '',
      diagnosis_age: condition.diagnosis_age || '',
      notes: condition.notes || '',
    });
    setShowConditionModal(true);
  };

  const handleDeleteCondition = async (familyMemberId, conditionId) => {
    if (!window.confirm('Are you sure you want to delete this condition?')) {
      return;
    }

    try {
      await apiService.deleteFamilyCondition(familyMemberId, conditionId);
      await refreshData();
    } catch (error) {
      console.error('Failed to delete family condition:', error);
      setError('Failed to delete condition');
    }
  };

  const handleConditionSubmit = async e => {
    e.preventDefault();

    const familyMemberId = selectedFamilyMember?.id || selectedFamilyMemberId;

    logger.debug('Submitting family condition', {
      selectedFamilyMember: selectedFamilyMember?.name,
      selectedFamilyMemberIdState: selectedFamilyMember?.id,
      selectedFamilyMemberIdBackup: selectedFamilyMemberId,
      finalFamilyMemberId: familyMemberId,
      conditionFormData,
      component: 'FamilyHistory',
    });

    if (!familyMemberId) {
      logger.error(
        'Family member information not available for condition submission',
        {
          selectedFamilyMember,
          selectedFamilyMemberId,
          component: 'FamilyHistory',
        }
      );
      setError('Family member information not available');
      return;
    }

    const conditionData = {
      condition_name: conditionFormData.condition_name,
      condition_type: conditionFormData.condition_type || null,
      severity: conditionFormData.severity || null,
      diagnosis_age: conditionFormData.diagnosis_age || null,
      notes: conditionFormData.notes || null,
    };

    try {
      if (editingCondition) {
        await apiService.updateFamilyCondition(
          familyMemberId,
          editingCondition.id,
          conditionData
        );
      } else {
        await apiService.createFamilyCondition(familyMemberId, conditionData);
      }

      setShowConditionModal(false);
      await refreshData();

      // Store the family member ID before clearing state
      const familyMemberIdToReopen = familyMemberId;

      // Clear the form state
      setConditionFormData({
        condition_name: '',
        condition_type: '',
        severity: '',
        diagnosis_age: '',
        notes: '',
      });
      setEditingCondition(null);
      setSelectedFamilyMember(null);
      setSelectedFamilyMemberId(null);

      // Reopen the view modal if we came from there
      if (openedFromViewModal && familyMemberIdToReopen) {
        const params = new URLSearchParams(location.search);
        params.set('view', familyMemberIdToReopen);
        navigate(`${location.pathname}?${params.toString()}`, {
          replace: true,
        });
      }
      setOpenedFromViewModal(false);
    } catch (error) {
      console.error('Failed to save family condition:', error);
      setError('Failed to save condition');
    }
  };

  const handleConditionCancel = () => {
    setConditionFormData({
      condition_name: '',
      condition_type: '',
      severity: '',
      diagnosis_age: '',
      notes: '',
    });
    setEditingCondition(null);
    setSelectedFamilyMember(null); // Reset this when canceling
    setSelectedFamilyMemberId(null);
    setOpenedFromViewModal(false);
    setShowConditionModal(false);
  };

  // View modal functions
  const handleViewFamilyMember = familyMember => {
    const params = new URLSearchParams(location.search);
    params.set('view', familyMember.id);
    navigate(`${location.pathname}?${params.toString()}`);
  };

  const handleCloseViewModal = () => {
    const params = new URLSearchParams(location.search);
    params.delete('view');
    const newSearch = params.toString();
    navigate(`${location.pathname}${newSearch ? `?${newSearch}` : ''}`);
  };

  // Updated condition functions to use URL parameter
  const handleAddConditionFromView = () => {
    if (viewingFamilyMember) {
      setSelectedFamilyMember(viewingFamilyMember);
      setSelectedFamilyMemberId(viewingFamilyMember.id);
      setOpenedFromViewModal(true);
      resetConditionForm();
      // Temporarily close view modal to prevent overlap
      const params = new URLSearchParams(location.search);
      params.delete('view');
      const newSearch = params.toString();
      navigate(`${location.pathname}${newSearch ? `?${newSearch}` : ''}`, {
        replace: true,
      });
      setShowConditionModal(true);
    }
  };

  const handleEditConditionFromView = condition => {
    if (viewingFamilyMember) {
      setSelectedFamilyMember(viewingFamilyMember);
      setSelectedFamilyMemberId(viewingFamilyMember.id);
      setOpenedFromViewModal(true);
      setEditingCondition(condition);
      setConditionFormData({
        condition_name: condition.condition_name || '',
        condition_type: condition.condition_type || '',
        severity: condition.severity || '',
        diagnosis_age: condition.diagnosis_age || '',
        notes: condition.notes || '',
      });
      // Temporarily close view modal to prevent overlap
      const params = new URLSearchParams(location.search);
      params.delete('view');
      const newSearch = params.toString();
      navigate(`${location.pathname}${newSearch ? `?${newSearch}` : ''}`, {
        replace: true,
      });
      setShowConditionModal(true);
    }
  };

  // Override the condition cancel to ensure we refresh data and reopen view modal
  const handleConditionCancelFromView = () => {
    setConditionFormData({
      condition_name: '',
      condition_type: '',
      severity: '',
      diagnosis_age: '',
      notes: '',
    });
    setEditingCondition(null);
    const familyMemberId = selectedFamilyMemberId;
    setSelectedFamilyMember(null);
    setSelectedFamilyMemberId(null);
    setShowConditionModal(false);

    // Reopen the view modal if we came from there
    if (openedFromViewModal && familyMemberId) {
      const params = new URLSearchParams(location.search);
      params.set('view', familyMemberId);
      navigate(`${location.pathname}?${params.toString()}`, { replace: true });
    }
    setOpenedFromViewModal(false);
  };

  // Group family members by relationship for better organization
  const groupedMembers = React.useMemo(() => {
    const groups = {
      Parents: ['father', 'mother'],
      Siblings: ['brother', 'sister'],
      Grandparents: [
        'paternal_grandfather',
        'paternal_grandmother',
        'maternal_grandfather',
        'maternal_grandmother',
      ],
      'Extended Family': ['uncle', 'aunt', 'cousin', 'other'],
    };

    return Object.entries(groups)
      .map(([groupName, relationships]) => ({
        name: groupName,
        members: dataManagement.data.filter(member =>
          relationships.includes(member.relationship)
        ),
      }))
      .filter(group => group.members.length > 0);
  }, [dataManagement.data]);

  // Flatten family members and conditions for table view
  const flattenedConditions = React.useMemo(() => {
    const conditions = [];
    
    dataManagement.data.forEach(member => {
      if (member.family_conditions && member.family_conditions.length > 0) {
        // Add each condition as a separate row
        member.family_conditions.forEach(condition => {
          conditions.push({
            id: `${member.id}-${condition.id}`, // Unique ID for table row
            familyMemberId: member.id,
            familyMemberName: member.name,
            relationship: member.relationship,
            gender: member.gender,
            birth_year: member.birth_year,
            death_year: member.death_year,
            is_deceased: member.is_deceased,
            // Condition data
            conditionId: condition.id,
            condition_name: condition.condition_name,
            condition_type: condition.condition_type,
            severity: condition.severity,
            diagnosis_age: condition.diagnosis_age,
            status: condition.status,
            notes: condition.notes,
            // For compatibility with existing table system
            created_at: condition.created_at,
            updated_at: condition.updated_at,
          });
        });
      } else {
        // Add family member with no conditions (empty row)
        conditions.push({
          id: `${member.id}-no-conditions`,
          familyMemberId: member.id,
          familyMemberName: member.name,
          relationship: member.relationship,
          gender: member.gender,
          birth_year: member.birth_year,
          death_year: member.death_year,
          is_deceased: member.is_deceased,
          // No condition data
          conditionId: null,
          condition_name: null,
          condition_type: null,
          severity: null,
          diagnosis_age: null,
          status: null,
          notes: null,
          created_at: member.created_at,
          updated_at: member.updated_at,
        });
      }
    });

    return conditions;
  }, [dataManagement.data]);

  const toggleExpanded = memberId => {
    const newExpanded = new Set(expandedMembers);
    if (newExpanded.has(memberId)) {
      newExpanded.delete(memberId);
    } else {
      newExpanded.add(memberId);
    }
    setExpandedMembers(newExpanded);
  };

  const getSeverityColor = severity => {
    switch (severity?.toLowerCase()) {
      case 'mild':
        return 'green';
      case 'moderate':
        return 'yellow';
      case 'severe':
        return 'red';
      case 'critical':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getConditionTypeColor = type => {
    switch (type?.toLowerCase()) {
      case 'cardiovascular':
        return 'red';
      case 'diabetes':
        return 'blue';
      case 'cancer':
        return 'purple';
      case 'mental_health':
        return 'teal';
      case 'neurological':
        return 'indigo';
      case 'genetic':
        return 'orange';
      default:
        return 'gray';
    }
  };

  const calculateAge = (birthYear, deathYear = null) => {
    const currentYear = new Date().getFullYear();
    const endYear = deathYear || currentYear;
    return birthYear ? endYear - birthYear : null;
  };

  if (loading) {
    return (
      <Center style={{ height: '200px' }}>
        <Loader size="md" />
      </Center>
    );
  }

  return (
    <Container size="xl">
      <PageHeader
        title="Family History"
        subtitle="Track medical conditions and health history of your family members"
        icon={<IconUsers size={24} />}
      />

      {error && (
        <Alert
          color="red"
          style={{ marginBottom: '1rem' }}
          onClose={clearError}
        >
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert color="green" style={{ marginBottom: '1rem' }}>
          {successMessage}
        </Alert>
      )}

      {/* Header Controls */}
      <div style={{ marginBottom: '1.5rem' }}>
        <Title order={3}>Family Medical History</Title>
        <Text size="sm" color="dimmed" mb="lg">
          {viewMode === 'table' 
            ? `${flattenedConditions.length} condition${flattenedConditions.length !== 1 ? 's' : ''} across ${dataManagement.data.length} family member${dataManagement.data.length !== 1 ? 's' : ''}`
            : `${dataManagement.data.length} family member${dataManagement.data.length !== 1 ? 's' : ''} recorded`
          }
        </Text>

        <Group justify="space-between" mb="lg">
          <Button
            leftIcon={<IconUserPlus size={16} />}
            onClick={handleAddMember}
            size="md"
          >
            Add Family Member
          </Button>

          <ViewToggle
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            showPrint={true}
          />
        </Group>
      </div>

      {/* Filters */}
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

      {/* Family Members Display */}
      {dataManagement.data.length === 0 ? (
        <Card shadow="sm" p="xl" style={{ textAlign: 'center' }}>
          <IconUsers size={48} color="var(--mantine-color-gray-5)" />
          <Title order={4} mt="md" color="dimmed">
            No Family Members Yet
          </Title>
          <Text color="dimmed" mb="lg">
            Start building your family medical history by adding your first
            family member.
          </Text>
          <Button
            leftIcon={<IconUserPlus size={16} />}
            onClick={handleAddMember}
          >
            Add Your First Family Member
          </Button>
        </Card>
      ) : viewMode === 'table' ? (
        <MedicalTable
          data={flattenedConditions}
          columns={[
            { header: 'Family Member', accessor: 'familyMemberName' },
            { header: 'Relationship', accessor: 'relationship' },
            { header: 'Condition', accessor: 'condition_name' },
            { header: 'Type', accessor: 'condition_type' },
            { header: 'Severity', accessor: 'severity' },
            { header: 'Diagnosis Age', accessor: 'diagnosis_age' },
            { header: 'Status', accessor: 'status' },
          ]}
          patientData={currentPatient}
          tableName="Family History"
          onView={(row) => handleViewFamilyMember({ id: row.familyMemberId })}
          onEdit={(row) => {
            if (row.conditionId) {
              // Edit condition
              const familyMember = familyMembers.find(m => m.id === row.familyMemberId);
              const condition = familyMember?.family_conditions?.find(c => c.id === row.conditionId);
              if (familyMember && condition) {
                handleEditCondition(familyMember, condition);
              }
            } else {
              // Edit family member (no condition)
              const familyMember = familyMembers.find(m => m.id === row.familyMemberId);
              if (familyMember) {
                handleEditMember(familyMember);
              }
            }
          }}
          onDelete={(row) => {
            if (row.conditionId) {
              // Delete condition
              handleDeleteCondition(row.familyMemberId, row.conditionId);
            } else {
              // Delete family member
              handleDeleteMember(row.familyMemberId);
            }
          }}
          formatters={{
            relationship: (value) => value?.replace('_', ' ') || '-',
            condition_name: (value) => value || 'No conditions',
            condition_type: (value) => value?.replace('_', ' ') || '-',
            severity: (value) => value || '-',
            diagnosis_age: (value) => value ? `${value} years` : '-',
            status: (value) => value || '-',
          }}
        />
      ) : (
        <Stack spacing="xl">
          {groupedMembers.map(group => (
            <div key={group.name}>
              <Group mb="md">
                <Title order={4} color="blue">
                  {group.name}
                </Title>
                <Badge variant="light" size="sm">
                  {group.members.length}
                </Badge>
              </Group>

              <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
                {group.members.map(member => {
                  const isExpanded = expandedMembers.has(member.id);
                  const conditionCount = member.family_conditions?.length || 0;
                  const age = calculateAge(
                    member.birth_year,
                    member.death_year
                  );

                  return (
                    <Card
                      key={member.id}
                      shadow="sm"
                      padding="md"
                      radius="md"
                      style={{ cursor: 'pointer' }}
                      onClick={() => toggleExpanded(member.id)}
                    >
                      <Group position="apart" mb="xs">
                        <div style={{ flex: 1 }}>
                          <Text weight={500} size="lg">
                            {member.name}
                          </Text>
                          <Text size="sm" color="dimmed" transform="capitalize">
                            {member.relationship.replace('_', ' ')}
                            {age && ` • Age ${age}`}
                            {member.is_deceased && ' • Deceased'}
                          </Text>
                        </div>

                        <Group spacing="xs">
                          <Button
                            size="xs"
                            variant="light"
                            onClick={e => {
                              e.stopPropagation();
                              handleViewFamilyMember(member);
                            }}
                          >
                            View Details
                          </Button>
                          <ActionIcon
                            variant="light"
                            onClick={e => {
                              e.stopPropagation();
                              handleEditMember(member);
                            }}
                          >
                            <IconEdit size={16} />
                          </ActionIcon>
                          <ActionIcon
                            variant="light"
                            color="red"
                            onClick={e => {
                              e.stopPropagation();
                              handleDeleteMember(member.id);
                            }}
                          >
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Group>
                      </Group>

                      <Group position="apart" mb={isExpanded ? 'md' : 0}>
                        <Badge
                          variant="light"
                          size="sm"
                          color={conditionCount > 0 ? 'blue' : 'gray'}
                        >
                          {conditionCount} Condition
                          {conditionCount !== 1 ? 's' : ''}
                        </Badge>
                        {isExpanded ? (
                          <IconChevronUp size={16} />
                        ) : (
                          <IconChevronDown size={16} />
                        )}
                      </Group>

                      <Collapse in={isExpanded}>
                        <Divider mb="md" />
                        <Text weight={500} mb="md">
                          Medical Conditions
                        </Text>

                        {conditionCount === 0 ? (
                          <Box
                            style={{ textAlign: 'center', padding: '1rem 0' }}
                          >
                            <Text size="sm" color="dimmed" mb="md">
                              No medical conditions recorded
                            </Text>
                            <Button
                              size="xs"
                              variant="light"
                              leftIcon={<IconStethoscope size={14} />}
                              onClick={e => {
                                e.stopPropagation();
                                handleAddCondition(member);
                              }}
                            >
                              Add Condition
                            </Button>
                          </Box>
                        ) : (
                          <Stack spacing="xs">
                            {member.family_conditions?.map(condition => (
                              <Box
                                key={condition.id}
                                p="xs"
                                style={{
                                  borderLeft: `3px solid var(--mantine-color-${getSeverityColor(condition.severity)}-6)`,
                                  backgroundColor:
                                    'var(--mantine-color-gray-0)',
                                  borderRadius: '4px',
                                }}
                              >
                                <Group position="apart">
                                  <div style={{ flex: 1 }}>
                                    <Group spacing="xs" mb="xs">
                                      <Text weight={500}>
                                        {condition.condition_name}
                                      </Text>
                                      {condition.severity && (
                                        <Badge
                                          size="xs"
                                          color={getSeverityColor(
                                            condition.severity
                                          )}
                                        >
                                          {condition.severity}
                                        </Badge>
                                      )}
                                      {condition.condition_type && (
                                        <Badge
                                          size="xs"
                                          variant="outline"
                                          color={getConditionTypeColor(
                                            condition.condition_type
                                          )}
                                        >
                                          {condition.condition_type.replace(
                                            '_',
                                            ' '
                                          )}
                                        </Badge>
                                      )}
                                    </Group>

                                    {condition.diagnosis_age && (
                                      <Text size="xs" color="dimmed">
                                        Diagnosed at age{' '}
                                        {condition.diagnosis_age}
                                      </Text>
                                    )}

                                    {condition.notes && (
                                      <Text
                                        size="xs"
                                        color="dimmed"
                                        lineClamp={2}
                                      >
                                        {condition.notes}
                                      </Text>
                                    )}
                                  </div>

                                  <Group spacing="xs">
                                    <ActionIcon
                                      size="xs"
                                      variant="light"
                                      onClick={e => {
                                        e.stopPropagation();
                                        handleEditCondition(member, condition);
                                      }}
                                    >
                                      <IconEdit size={12} />
                                    </ActionIcon>
                                    <ActionIcon
                                      size="xs"
                                      variant="light"
                                      color="red"
                                      onClick={e => {
                                        e.stopPropagation();
                                        handleDeleteCondition(
                                          member.id,
                                          condition.id
                                        );
                                      }}
                                    >
                                      <IconTrash size={12} />
                                    </ActionIcon>
                                  </Group>
                                </Group>
                              </Box>
                            ))}
                          </Stack>
                        )}
                      </Collapse>
                    </Card>
                  );
                })}
              </SimpleGrid>
            </div>
          ))}
        </Stack>
      )}

      {/* Family Member Form Modal */}
      <MantineFamilyMemberForm
        isOpen={showModal}
        onClose={handleCancel}
        title={editingMember ? 'Edit Family Member' : 'Add Family Member'}
        formData={formData}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
        editingMember={editingMember}
        fieldErrors={fieldErrors}
      />

      {/* Family Condition Form Modal */}
      <MantineFamilyConditionForm
        isOpen={showConditionModal}
        onClose={
          viewingFamilyMemberId
            ? handleConditionCancelFromView
            : handleConditionCancel
        }
        title={
          editingCondition
            ? `Edit Condition for ${selectedFamilyMember?.name}`
            : `Add Condition for ${selectedFamilyMember?.name}`
        }
        formData={conditionFormData}
        onInputChange={handleConditionInputChange}
        onSubmit={handleConditionSubmit}
        editingCondition={editingCondition}
      />

      {/* Family Member View Modal */}
      {viewingFamilyMember && (
        <Modal
          opened={!!viewingFamilyMemberId}
          onClose={handleCloseViewModal}
          title={`${viewingFamilyMember.name} - Family Medical History`}
          size="lg"
          zIndex={1000}
        >
          <Stack spacing="md">
            {/* Family Member Info */}
            <Card withBorder p="md">
              <Group position="apart" mb="xs">
                <Text weight={500} size="lg">
                  {viewingFamilyMember.name}
                </Text>
                <Group spacing="xs">
                  <ActionIcon
                    variant="light"
                    onClick={() => handleEditMember(viewingFamilyMember)}
                  >
                    <IconEdit size={16} />
                  </ActionIcon>
                </Group>
              </Group>

              <Stack spacing="xs">
                <Text size="sm">
                  <strong>Relationship:</strong>{' '}
                  {viewingFamilyMember.relationship?.replace('_', ' ')}
                </Text>
                {viewingFamilyMember.gender && (
                  <Text size="sm">
                    <strong>Gender:</strong> {viewingFamilyMember.gender}
                  </Text>
                )}
                {viewingFamilyMember.birth_year && (
                  <Text size="sm">
                    <strong>Birth Year:</strong>{' '}
                    {viewingFamilyMember.birth_year}
                    {calculateAge(
                      viewingFamilyMember.birth_year,
                      viewingFamilyMember.death_year
                    ) &&
                      ` (Age ${calculateAge(viewingFamilyMember.birth_year, viewingFamilyMember.death_year)})`}
                  </Text>
                )}
                {viewingFamilyMember.is_deceased &&
                  viewingFamilyMember.death_year && (
                    <Text size="sm">
                      <strong>Death Year:</strong>{' '}
                      {viewingFamilyMember.death_year}
                    </Text>
                  )}
                {viewingFamilyMember.notes && (
                  <Text size="sm">
                    <strong>Notes:</strong> {viewingFamilyMember.notes}
                  </Text>
                )}
              </Stack>
            </Card>

            {/* Medical Conditions Section */}
            <Card withBorder p="md">
              <Group position="apart" mb="md">
                <Text weight={500} size="lg">
                  Medical Conditions
                </Text>
                <Button
                  size="sm"
                  leftIcon={<IconStethoscope size={16} />}
                  onClick={handleAddConditionFromView}
                >
                  Add Condition
                </Button>
              </Group>

              {!viewingFamilyMember.family_conditions ||
              viewingFamilyMember.family_conditions.length === 0 ? (
                <Text
                  size="sm"
                  color="dimmed"
                  style={{ textAlign: 'center', padding: '2rem 0' }}
                >
                  No medical conditions recorded
                </Text>
              ) : (
                <Stack spacing="md">
                  {viewingFamilyMember.family_conditions.map(condition => (
                    <Box
                      key={condition.id}
                      p="md"
                      style={{
                        borderLeft: `4px solid var(--mantine-color-${getSeverityColor(condition.severity)}-6)`,
                        backgroundColor: 'var(--mantine-color-gray-0)',
                        borderRadius: '8px',
                      }}
                    >
                      <Group position="apart" mb="xs">
                        <Group spacing="xs">
                          <Text weight={500} size="md">
                            {condition.condition_name}
                          </Text>
                          {condition.severity && (
                            <Badge color={getSeverityColor(condition.severity)}>
                              {condition.severity}
                            </Badge>
                          )}
                          {condition.condition_type && (
                            <Badge
                              variant="outline"
                              color={getConditionTypeColor(
                                condition.condition_type
                              )}
                            >
                              {condition.condition_type.replace('_', ' ')}
                            </Badge>
                          )}
                        </Group>

                        <Group spacing="xs">
                          <ActionIcon
                            variant="light"
                            onClick={() =>
                              handleEditConditionFromView(condition)
                            }
                          >
                            <IconEdit size={16} />
                          </ActionIcon>
                          <ActionIcon
                            variant="light"
                            color="red"
                            onClick={() =>
                              handleDeleteCondition(
                                viewingFamilyMember.id,
                                condition.id
                              )
                            }
                          >
                            <IconTrash size={16} />
                          </ActionIcon>
                        </Group>
                      </Group>

                      {condition.diagnosis_age && (
                        <Text size="sm" color="dimmed" mb="xs">
                          Diagnosed at age {condition.diagnosis_age}
                        </Text>
                      )}

                      {condition.notes && (
                        <Text size="sm" color="dimmed">
                          {condition.notes}
                        </Text>
                      )}
                    </Box>
                  ))}
                </Stack>
              )}
            </Card>
          </Stack>
        </Modal>
      )}
    </Container>
  );
};

export default FamilyHistory;
