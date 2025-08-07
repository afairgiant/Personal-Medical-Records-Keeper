import React from 'react';
import {
  Modal,
  Stack,
  Title,
  Text,
  Paper,
  Group,
  Button,
  Card,
  Divider,
  Grid,
  Badge,
} from '@mantine/core';
import DocumentSection from '../../shared/DocumentSection';
import { formatDate } from '../../../utils/helpers';
import { navigateToEntity } from '../../../utils/linkNavigation';
import logger from '../../../services/logger';

const VisitViewModal = ({
  isOpen,
  onClose,
  visit,
  onEdit,
  practitioners,
  conditions,
  navigate,
  onFileUploadComplete,
  isBlocking,
  onError
}) => {
  const handleError = (error, context) => {
    logger.error('visit_view_modal_error', {
      message: `Error in VisitViewModal: ${context}`,
      visitId: visit?.id,
      error: error.message,
      component: 'VisitViewModal',
    });
    
    if (onError) {
      onError(error);
    }
  };

  const handleDocumentError = (error) => {
    handleError(error, 'document_manager');
  };

  const handleDocumentUploadComplete = (success, completedCount, failedCount) => {
    logger.info('visits_view_upload_completed', {
      message: 'File upload completed in visits view',
      visitId: visit?.id,
      success,
      completedCount,
      failedCount,
      component: 'VisitViewModal',
    });
    
    if (onFileUploadComplete) {
      onFileUploadComplete(success, completedCount, failedCount);
    }
  };

  const getPractitionerDisplay = (practitionerId) => {
    if (!practitionerId) return 'No practitioner assigned';

    const practitioner = practitioners.find(
      p => p.id === parseInt(practitionerId)
    );
    if (practitioner) {
      return `${practitioner.name}${practitioner.specialty ? ` - ${practitioner.specialty}` : ''}`;
    }
    return `Practitioner ID: ${practitionerId}`;
  };

  const getConditionDetails = (conditionId) => {
    if (!conditionId || !conditions) return null;
    return conditions.find(c => c.id === conditionId);
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'red';
      case 'high':
        return 'orange';
      case 'medium':
        return 'yellow';
      case 'low':
        return 'blue';
      default:
        return 'gray';
    }
  };

  const getVisitTypeColor = (visitType) => {
    switch (visitType?.toLowerCase()) {
      case 'emergency':
        return 'red';
      case 'urgent care':
        return 'orange';
      case 'follow-up':
        return 'blue';
      case 'routine':
        return 'green';
      case 'consultation':
        return 'purple';
      default:
        return 'gray';
    }
  };

  if (!visit) return null;

  try {
    const practitioner = practitioners.find(p => p.id === parseInt(visit.practitioner_id));
    const condition = getConditionDetails(visit.condition_id);

    return (
      <Modal
        opened={isOpen}
        onClose={() => !isBlocking && onClose()}
        title={
          <Group>
            <Text size="lg" fw={600}>
              Visit Details
            </Text>
            <Group gap="xs">
              {visit.visit_type && (
                <Badge
                  color={getVisitTypeColor(visit.visit_type)}
                  variant="light"
                  size="sm"
                >
                  {visit.visit_type}
                </Badge>
              )}
              {visit.priority && (
                <Badge
                  color={getPriorityColor(visit.priority)}
                  variant="filled"
                  size="sm"
                >
                  {visit.priority}
                </Badge>
              )}
            </Group>
          </Group>
        }
        size="lg"
        centered
      >
        <Stack gap="md">
          {/* Header Card */}
          <Card withBorder p="md" style={{ backgroundColor: '#f8f9fa' }}>
            <Group justify="space-between" align="flex-start">
              <Stack gap="xs" style={{ flex: 1 }}>
                <Title order={3}>
                  {visit.reason || 'General Visit'}
                </Title>
                <Text size="sm" c="dimmed">
                  {formatDate(visit.date)}
                </Text>
              </Stack>
            </Group>
          </Card>

          {/* Visit Information Grid */}
          <Grid>
            <Grid.Col span={6}>
              <Card withBorder p="md" h="100%">
                <Stack gap="sm">
                  <Text fw={600} size="sm" c="dimmed">
                    VISIT INFORMATION
                  </Text>
                  <Divider />
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Reason:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.reason ? 'inherit' : 'dimmed'}
                    >
                      {visit.reason || 'Not specified'}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Visit Type:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.visit_type ? 'inherit' : 'dimmed'}
                    >
                      {visit.visit_type || 'Not specified'}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Priority:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.priority ? 'inherit' : 'dimmed'}
                    >
                      {visit.priority || 'Not specified'}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Location:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.location ? 'inherit' : 'dimmed'}
                    >
                      {visit.location || 'Not specified'}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Duration:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.duration_minutes ? 'inherit' : 'dimmed'}
                    >
                      {visit.duration_minutes
                        ? `${visit.duration_minutes} minutes`
                        : 'Not specified'}
                    </Text>
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={6}>
              <Card withBorder p="md" h="100%">
                <Stack gap="sm">
                  <Text fw={600} size="sm" c="dimmed">
                    CLINICAL DETAILS
                  </Text>
                  <Divider />
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Practitioner:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.practitioner_id ? 'inherit' : 'dimmed'}
                    >
                      {visit.practitioner_id
                        ? getPractitionerDisplay(visit.practitioner_id)
                        : 'Not specified'}
                    </Text>
                  </Group>
                  {condition && (
                    <Group>
                      <Text size="sm" fw={500} w={80}>
                        Condition:
                      </Text>
                      <Text
                        size="sm"
                        c="blue"
                        style={{ cursor: 'pointer', textDecoration: 'underline' }}
                        onClick={() => navigateToEntity('condition', condition.id, navigate)}
                        title="View condition details"
                      >
                        {condition.diagnosis}
                      </Text>
                    </Group>
                  )}
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Practice:
                    </Text>
                    <Text
                      size="sm"
                      c={practitioner?.specialty ? 'inherit' : 'dimmed'}
                    >
                      {practitioner?.specialty || 'Not specified'}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Chief Complaint:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.chief_complaint ? 'inherit' : 'dimmed'}
                    >
                      {visit.chief_complaint || 'Not specified'}
                    </Text>
                  </Group>
                  <Group>
                    <Text size="sm" fw={500} w={80}>
                      Diagnosis:
                    </Text>
                    <Text
                      size="sm"
                      c={visit.diagnosis ? 'inherit' : 'dimmed'}
                    >
                      {visit.diagnosis || 'Not specified'}
                    </Text>
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>

          {/* Treatment Plan Section */}
          {visit.treatment_plan && (
            <Card withBorder p="md">
              <Stack gap="sm">
                <Text fw={600} size="sm" c="dimmed">
                  TREATMENT PLAN
                </Text>
                <Divider />
                <Text
                  size="sm"
                  style={{ whiteSpace: 'pre-wrap' }}
                  c={visit.treatment_plan ? 'inherit' : 'dimmed'}
                >
                  {visit.treatment_plan || 'No treatment plan available'}
                </Text>
              </Stack>
            </Card>
          )}

          {/* Follow-up Instructions Section */}
          {visit.follow_up_instructions && (
            <Card withBorder p="md">
              <Stack gap="sm">
                <Text fw={600} size="sm" c="dimmed">
                  FOLLOW-UP INSTRUCTIONS
                </Text>
                <Divider />
                <Text
                  size="sm"
                  style={{ whiteSpace: 'pre-wrap' }}
                  c={visit.follow_up_instructions ? 'inherit' : 'dimmed'}
                >
                  {visit.follow_up_instructions || 'No follow-up instructions available'}
                </Text>
              </Stack>
            </Card>
          )}

          {/* Additional Notes Section */}
          <Card withBorder p="md">
            <Stack gap="sm">
              <Text fw={600} size="sm" c="dimmed">
                ADDITIONAL NOTES
              </Text>
              <Divider />
              <Text 
                size="sm" 
                style={{ whiteSpace: 'pre-wrap' }}
                c={visit.notes ? 'inherit' : 'dimmed'}
              >
                {visit.notes || 'No notes available'}
              </Text>
            </Stack>
          </Card>

          {/* Document Management Section */}
          <DocumentSection
            entityType="visit"
            entityId={visit.id}
            mode="view"
            onUploadComplete={handleDocumentUploadComplete}
            onError={handleDocumentError}
          />

          {/* Action Buttons */}
          <Group justify="flex-end" mt="md">
            <Button
              variant="filled"
              size="xs"
              onClick={() => {
                onClose();
                // Small delay to ensure view modal is closed before opening edit modal
                setTimeout(() => {
                  onEdit(visit);
                }, 100);
              }}
            >
              Edit Visit
            </Button>
            <Button variant="filled" size="xs" onClick={onClose}>
              Close
            </Button>
          </Group>
        </Stack>
      </Modal>
    );
  } catch (error) {
    handleError(error, 'render');
    return null;
  }
};

export default VisitViewModal;