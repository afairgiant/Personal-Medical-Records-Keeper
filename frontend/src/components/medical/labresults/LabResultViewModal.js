import React from 'react';
import {
  Modal,
  Stack,
  Title,
  SimpleGrid,
  Text,
  Paper,
  Group,
  Button,
  ScrollArea,
  Card,
  Divider,
  Badge,
} from '@mantine/core';
import StatusBadge from '../StatusBadge';
import ConditionRelationships from '../ConditionRelationships';
import DocumentSection from '../../shared/DocumentSection';
import { formatDate } from '../../../utils/helpers';
import logger from '../../../services/logger';

const LabResultViewModal = ({
  isOpen,
  onClose,
  labResult,
  onEdit,
  practitioners,
  onFileUploadComplete,
  conditions,
  labResultConditions,
  fetchLabResultConditions,
  navigate,
  currentPatient,
  isBlocking,
  onError
}) => {
  const handleError = (error, context) => {
    logger.error('lab_result_view_modal_error', {
      message: `Error in LabResultViewModal: ${context}`,
      labResultId: labResult?.id,
      error: error.message,
      component: 'LabResultViewModal',
    });
    
    if (onError) {
      onError(error);
    }
  };

  const handleDocumentError = (error) => {
    logger.error('lab_result_document_error_details', {
      message: 'Detailed document manager error in lab result view modal',
      labResultId: labResult?.id,
      error: error,
      errorMessage: error?.message,
      errorStack: error?.stack,
      errorDetails: error?.details,
      errorResponse: error?.response,
      component: 'LabResultViewModal',
    });
    handleError(error, 'document_manager');
  };

  if (!labResult) return null;

  try {
    // Find practitioner for this lab result
    const practitioner = practitioners.find(p => p.id === labResult.practitioner_id);

    return (
      <Modal
        opened={isOpen}
        onClose={() => !isBlocking && onClose()}
        title={labResult.test_name || 'Lab Result Details'}
        size="xl"
        scrollAreaComponent={ScrollArea.Autosize}
        centered
      >
        <Stack gap="lg">
          {/* Header Card */}
          <Paper withBorder p="md" style={{ backgroundColor: '#f8f9fa' }}>
            <Group justify="space-between" align="center">
              <div>
                <Title order={3} mb="xs">{labResult.test_name}</Title>
                <Group gap="xs">
                  {labResult.test_category && (
                    <StatusBadge status={labResult.test_category} />
                  )}
                  <StatusBadge status={labResult.status} />
                </Group>
              </div>
              {labResult.labs_result && (
                <StatusBadge status={labResult.labs_result} size="lg" />
              )}
            </Group>
          </Paper>

          {/* Test Information Section */}
          <div>
            <Title order={4} mb="sm">Test Information</Title>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Test Code</Text>
                <Text>{labResult.test_code || 'N/A'}</Text>
              </Stack>
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Category</Text>
                <Text>{labResult.test_category || 'N/A'}</Text>
              </Stack>
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Test Type</Text>
                <Text c={labResult.test_type ? 'inherit' : 'dimmed'}>
                  {labResult.test_type || 'Not specified'}
                </Text>
              </Stack>
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Facility</Text>
                <Text c={labResult.facility ? 'inherit' : 'dimmed'}>
                  {labResult.facility || 'Not specified'}
                </Text>
              </Stack>
            </SimpleGrid>
          </div>

          {/* Test Results Section */}
          <div>
            <Title order={4} mb="sm">Test Results</Title>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Status</Text>
                <StatusBadge status={labResult.status} />
              </Stack>
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Lab Result</Text>
                {labResult.labs_result ? (
                  <StatusBadge status={labResult.labs_result} />
                ) : (
                  <Text c="dimmed">Not specified</Text>
                )}
              </Stack>
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Ordered Date</Text>
                <Text>{formatDate(labResult.ordered_date)}</Text>
              </Stack>
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Completed Date</Text>
                <Text c={labResult.completed_date ? 'inherit' : 'dimmed'}>
                  {labResult.completed_date
                    ? formatDate(labResult.completed_date)
                    : 'Not completed'}
                </Text>
              </Stack>
            </SimpleGrid>
          </div>

          {/* Practitioner Information Section */}
          <div>
            <Title order={4} mb="sm">Ordering Practitioner</Title>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              <Stack gap="xs">
                <Text fw={500} size="sm" c="dimmed">Doctor</Text>
                <Text c={labResult.practitioner_id ? 'inherit' : 'dimmed'}>
                  {labResult.practitioner_id
                    ? practitioner?.name || `Practitioner ID: ${labResult.practitioner_id}`
                    : 'Not specified'}
                </Text>
              </Stack>
              {practitioner?.specialty && (
                <Stack gap="xs">
                  <Text fw={500} size="sm" c="dimmed">Specialty</Text>
                  <Text>{practitioner.specialty}</Text>
                </Stack>
              )}
            </SimpleGrid>
          </div>

          {/* Notes Section */}
          <div>
            <Title order={4} mb="sm">Notes</Title>
            <Paper withBorder p="sm" bg="gray.1">
              <Text
                style={{ whiteSpace: 'pre-wrap' }}
                c={labResult.notes ? 'inherit' : 'dimmed'}
              >
                {labResult.notes || 'No notes available'}
              </Text>
            </Paper>
          </div>

          {/* Related Conditions Section */}
          {fetchLabResultConditions && (
            <div>
              <Title order={4} mb="sm">Related Conditions</Title>
              <ConditionRelationships
                labResultId={labResult.id}
                labResultConditions={labResultConditions}
                conditions={conditions}
                fetchLabResultConditions={fetchLabResultConditions}
                navigate={navigate}
                currentPatient={currentPatient}
                isViewMode={true}
              />
            </div>
          )}

          {/* Document Management Section */}
          <DocumentSection
            entityType="lab-result"
            entityId={labResult.id}
            mode="view"
            onUploadComplete={onFileUploadComplete}
            onError={handleDocumentError}
          />

          {/* Action Buttons */}
          <Group justify="space-between" mt="md">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            <Button 
              onClick={() => { 
                onClose(); 
                onEdit(labResult); 
              }}
            >
              Edit Lab Result
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

export default LabResultViewModal;