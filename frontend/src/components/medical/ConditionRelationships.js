import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { navigateToEntity } from '../../utils/linkNavigation';
import {
  Badge,
  Button,
  Group,
  Stack,
  Text,
  Paper,
  TextInput,
  ActionIcon,
  Alert,
  MultiSelect,
  Textarea,
  Modal,
  Title,
} from '@mantine/core';
import {
  IconPlus,
  IconTrash,
  IconEdit,
  IconCheck,
  IconX,
  IconStethoscope,
  IconInfoCircle,
} from '@tabler/icons-react';

const ConditionRelationships = ({
  labResultId,
  labResultConditions = {},
  conditions = [],
  fetchLabResultConditions,
  navigate,
  currentPatient,
  isViewMode = false, // New prop to distinguish between view and edit modes
}) => {
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState(null);
  const [newRelationship, setNewRelationship] = useState({
    condition_id: '',
    relevance_note: '',
  });
  const [error, setError] = useState(null);

  // Get relationships for this lab result
  useEffect(() => {
    const labRelationships = labResultConditions[labResultId] || [];
    setRelationships(labRelationships);
  }, [labResultId, labResultConditions]);

  // Load relationships when component mounts
  useEffect(() => {
    if (labResultId && fetchLabResultConditions) {
      fetchLabResultConditions(labResultId);
    }
  }, [labResultId]); // Remove fetchLabResultConditions from dependencies to prevent infinite loop

  const handleAddRelationship = async () => {
    if (!newRelationship.condition_id) {
      setError('Please select a condition');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiService.createLabResultCondition(labResultId, {
        lab_result_id: labResultId,
        condition_id: parseInt(newRelationship.condition_id),
        relevance_note: newRelationship.relevance_note || null,
      }, null, currentPatient?.id);

      // Refresh relationships
      if (fetchLabResultConditions) {
        await fetchLabResultConditions(labResultId);
      }

      // Reset form and close modal
      setNewRelationship({ condition_id: '', relevance_note: '' });
      setShowAddModal(false);
    } catch (err) {
      setError(err.message || 'Failed to add condition relationship');
    } finally {
      setLoading(false);
    }
  };

  const handleEditRelationship = async (relationshipId, updates) => {
    setLoading(true);
    setError(null);

    try {
      await apiService.updateLabResultCondition(labResultId, relationshipId, updates);

      // Refresh relationships
      if (fetchLabResultConditions) {
        await fetchLabResultConditions(labResultId);
      }

      setEditingRelationship(null);
    } catch (err) {
      setError(err.message || 'Failed to update condition relationship');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRelationship = async (relationshipId) => {
    if (!window.confirm('Are you sure you want to remove this condition relationship?')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiService.deleteLabResultCondition(labResultId, relationshipId);

      // Refresh relationships
      if (fetchLabResultConditions) {
        await fetchLabResultConditions(labResultId);
      }
    } catch (err) {
      setError(err.message || 'Failed to delete condition relationship');
    } finally {
      setLoading(false);
    }
  };

  const getConditionById = (conditionId) => {
    return conditions.find(condition => condition.id === conditionId);
  };

  // Prepare condition options for MultiSelect
  const conditionOptions = conditions.map(condition => ({
    value: condition.id.toString(),
    label: `${condition.diagnosis}${condition.status ? ` (${condition.status})` : ''}`,
  }));

  // Filter out already linked conditions
  const linkedConditionIds = relationships.map(rel => rel.condition_id.toString());
  const availableConditionOptions = conditionOptions.filter(
    option => !linkedConditionIds.includes(option.value)
  );

  return (
    <Stack gap="md">
      {error && (
        <Alert icon={<IconInfoCircle size={16} />} color="red" variant="light">
          {error}
        </Alert>
      )}

      {/* Existing Relationships */}
      {relationships.length > 0 ? (
        <Stack gap="sm">
          {relationships.map(relationship => {
            const condition = relationship.condition || getConditionById(relationship.condition_id);
            const isEditing = editingRelationship?.id === relationship.id;

            return (
              <Paper key={relationship.id} withBorder p="md">
                <Group justify="space-between" align="flex-start">
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Group gap="sm">
                      {isViewMode ? (
                        <Text
                          size="sm"
                          fw={500}
                          c="blue"
                          style={{ cursor: 'pointer', textDecoration: 'underline' }}
                          onClick={() => navigateToEntity('condition', condition?.id, navigate)}
                        >
                          {condition?.diagnosis || `Condition ID: ${relationship.condition_id}`}
                        </Text>
                      ) : (
                        <Badge
                          variant="light"
                          color="blue"
                          leftSection={<IconStethoscope size={12} />}
                          style={{ cursor: 'pointer' }}
                          onClick={() => navigateToEntity('condition', condition?.id, navigate)}
                        >
                          {condition?.diagnosis || `Condition ID: ${relationship.condition_id}`}
                        </Badge>
                      )}
                      {condition?.status && (
                        <Badge variant="outline" size="sm">
                          {condition.status}
                        </Badge>
                      )}
                      {condition?.severity && (
                        <Badge variant="outline" size="sm" color="orange">
                          {condition.severity}
                        </Badge>
                      )}
                    </Group>

                    {!isViewMode && isEditing ? (
                      <Textarea
                        placeholder="Relevance note (optional)"
                        value={editingRelationship?.relevance_note || relationship.relevance_note || ''}
                        onChange={(e) => setEditingRelationship({
                          ...editingRelationship,
                          relevance_note: e.target.value
                        })}
                        size="sm"
                        autosize
                        minRows={2}
                      />
                    ) : relationship.relevance_note ? (
                      <Text size="sm" c="dimmed" fs="italic">
                        {relationship.relevance_note}
                      </Text>
                    ) : !isViewMode ? (
                      <Text size="sm" c="dimmed">
                        No relevance note provided
                      </Text>
                    ) : null}
                  </Stack>

                  {!isViewMode && (
                    <Group gap="xs">
                      {isEditing ? (
                        <>
                          <ActionIcon
                            variant="light"
                            color="green"
                            size="sm"
                            onClick={() => handleEditRelationship(relationship.id, {
                              relevance_note: editingRelationship?.relevance_note || relationship.relevance_note
                            })}
                            loading={loading}
                          >
                            <IconCheck size={14} />
                          </ActionIcon>
                          <ActionIcon
                            variant="light"
                            color="gray"
                            size="sm"
                            onClick={() => setEditingRelationship(null)}
                          >
                            <IconX size={14} />
                          </ActionIcon>
                        </>
                      ) : (
                        <>
                          <ActionIcon
                            variant="light"
                            color="blue"
                            size="sm"
                            onClick={() => setEditingRelationship({
                              id: relationship.id,
                              relevance_note: relationship.relevance_note || ''
                            })}
                          >
                            <IconEdit size={14} />
                          </ActionIcon>
                          <ActionIcon
                            variant="light"
                            color="red"
                            size="sm"
                            onClick={() => handleDeleteRelationship(relationship.id)}
                            loading={loading}
                          >
                            <IconTrash size={14} />
                          </ActionIcon>
                        </>
                      )}
                    </Group>
                  )}
                </Group>
              </Paper>
            );
          })}
        </Stack>
      ) : (
        <Paper withBorder p="md" ta="center">
          <Text c="dimmed">No conditions linked to this lab result</Text>
        </Paper>
      )}

      {/* Add New Relationship Button */}
      {!isViewMode && availableConditionOptions.length > 0 && (
        <Button
          variant="light"
          leftSection={<IconPlus size={16} />}
          onClick={() => setShowAddModal(true)}
          disabled={loading}
        >
          Link Condition
        </Button>
      )}

      {/* Add Relationship Modal */}
      <Modal
        opened={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          setNewRelationship({ condition_id: '', relevance_note: '' });
          setError(null);
        }}
        title="Link Condition to Lab Result"
        size="md"
        centered
      >
        <Stack gap="md">
          <MultiSelect
            label="Select Condition"
            placeholder="Choose a condition to link"
            data={availableConditionOptions}
            value={newRelationship.condition_id ? [newRelationship.condition_id] : []}
            onChange={(values) => setNewRelationship(prev => ({
              ...prev,
              condition_id: values[0] || ''
            }))}
            searchable
            clearable
            required
          />

          <Textarea
            label="Relevance Note"
            placeholder="Describe how this condition relates to the lab result (optional)"
            value={newRelationship.relevance_note}
            onChange={(e) => setNewRelationship(prev => ({
              ...prev,
              relevance_note: e.target.value
            }))}
            autosize
            minRows={3}
          />

          <Group justify="flex-end" gap="sm">
            <Button
              variant="light"
              onClick={() => {
                setShowAddModal(false);
                setNewRelationship({ condition_id: '', relevance_note: '' });
                setError(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddRelationship}
              loading={loading}
              disabled={!newRelationship.condition_id}
            >
              Link Condition
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
};

export default ConditionRelationships;