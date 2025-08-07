import React from 'react';
import {
  Modal,
  Stack,
  Card,
  Group,
  Text,
  Title,
  Badge,
  Divider,
  Button,
  Grid
} from '@mantine/core';
import StatusBadge from '../StatusBadge';
import DocumentSection from '../../shared/DocumentSection';
import { formatDate } from '../../../utils/helpers';
import { navigateToEntity } from '../../../utils/linkNavigation';
import logger from '../../../services/logger';

const ProcedureViewModal = ({
  isOpen,
  onClose,
  procedure,
  onEdit,
  practitioners,
  navigate,
  onFileUploadComplete,
  onError
}) => {
  const handleError = (error, context) => {
    logger.error('procedure_view_modal_error', {
      message: `Error in ProcedureViewModal during ${context}`,
      procedureId: procedure?.id,
      error: error.message,
      component: 'ProcedureViewModal',
    });
    
    if (onError) {
      onError(error);
    }
  };

  const handleDocumentError = (error) => {
    handleError(error, 'document_management');
  };

  const handleDocumentUploadComplete = (success, completedCount, failedCount) => {
    logger.info('procedures_view_upload_completed', {
      message: 'File upload completed in procedures view',
      procedureId: procedure?.id,
      success,
      completedCount,
      failedCount,
      component: 'ProcedureViewModal',
    });
    
    if (onFileUploadComplete) {
      onFileUploadComplete(success, completedCount, failedCount);
    }
  };

  const handleEditClick = () => {
    try {
      onClose();
      onEdit(procedure);
    } catch (error) {
      handleError(error, 'edit_navigation');
    }
  };

  if (!procedure) {
    return null;
  }

  try {
    // Find practitioner for this procedure
    const practitioner = practitioners.find(p => p.id === procedure.practitioner_id);

    return (
      <Modal
        opened={isOpen}
        onClose={onClose}
        title={
          <Group>
            <Text size="lg" fw={600}>
              Procedure Details
            </Text>
            <StatusBadge status={procedure.status} />
          </Group>
        }
        size="lg"
        centered
      >
        <Stack gap="md">
          {/* Header Card */}
          <Card withBorder p="md" style={{ backgroundColor: '#f8f9fa' }}>
            <Stack gap="sm">
              <Group justify="space-between" align="flex-start">
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Title order={3}>{procedure.procedure_name}</Title>
                  <Group gap="xs">
                    {procedure.procedure_type && (
                      <Badge variant="light" color="blue" size="lg">
                        {procedure.procedure_type}
                      </Badge>
                    )}
                    {procedure.procedure_code && (
                      <Badge variant="light" color="teal" size="lg">
                        {procedure.procedure_code}
                      </Badge>
                    )}
                  </Group>
                </Stack>
              </Group>
            </Stack>
          </Card>

          {/* Information Sections */}
          <Grid>
            <Grid.Col span={6}>
              <Card withBorder p="md">
                <Stack gap="sm">
                  <Text fw={600} size="sm" c="dimmed">
                    PROCEDURE INFORMATION
                  </Text>
                  <Divider />
                  <Stack gap="xs">
                    <Group>
                      <Text size="sm" fw={500} w={100}>
                        Date:
                      </Text>
                      <Text
                        size="sm"
                        c={procedure.date ? 'inherit' : 'dimmed'}
                      >
                        {procedure.date ? formatDate(procedure.date) : 'Not specified'}
                      </Text>
                    </Group>
                    <Group>
                      <Text size="sm" fw={500} w={100}>
                        Setting:
                      </Text>
                      {procedure.procedure_setting ? (
                        <Badge variant="light" color="cyan" size="sm">
                          {procedure.procedure_setting}
                        </Badge>
                      ) : (
                        <Text size="sm" c="dimmed">
                          Not specified
                        </Text>
                      )}
                    </Group>
                    <Group>
                      <Text size="sm" fw={500} w={100}>
                        Duration:
                      </Text>
                      <Text
                        size="sm"
                        c={procedure.procedure_duration ? 'inherit' : 'dimmed'}
                      >
                        {procedure.procedure_duration
                          ? `${procedure.procedure_duration} minutes`
                          : 'Not specified'}
                      </Text>
                    </Group>
                    <Group>
                      <Text size="sm" fw={500} w={100}>
                        Facility:
                      </Text>
                      <Text
                        size="sm"
                        c={procedure.facility ? 'inherit' : 'dimmed'}
                      >
                        {procedure.facility || 'Not specified'}
                      </Text>
                    </Group>
                  </Stack>
                </Stack>
              </Card>
            </Grid.Col>

            <Grid.Col span={6}>
              <Card withBorder p="md">
                <Stack gap="sm">
                  <Text fw={600} size="sm" c="dimmed">
                    PRACTITIONER INFORMATION
                  </Text>
                  <Divider />
                  <Stack gap="xs">
                    <Group>
                      <Text size="sm" fw={500} w={100}>
                        Doctor:
                      </Text>
                      <Text
                        size="sm"
                        c={procedure.practitioner_id ? 'blue' : 'dimmed'}
                        style={procedure.practitioner_id ? { cursor: 'pointer', textDecoration: 'underline' } : {}}
                        onClick={procedure.practitioner_id ? () => navigateToEntity('practitioner', procedure.practitioner_id, navigate) : undefined}
                        title={procedure.practitioner_id ? "View practitioner details" : undefined}
                      >
                        {procedure.practitioner_id
                          ? practitioner?.name || `Practitioner ID: ${procedure.practitioner_id}`
                          : 'Not specified'}
                      </Text>
                    </Group>
                    <Group>
                      <Text size="sm" fw={500} w={100}>
                        Specialty:
                      </Text>
                      <Text
                        size="sm"
                        c={procedure.practitioner_id ? 'inherit' : 'dimmed'}
                      >
                        {procedure.practitioner_id
                          ? practitioner?.specialty || 'Not specified'
                          : 'Not specified'}
                      </Text>
                    </Group>
                  </Stack>
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>

          {/* Description Section */}
          <Card withBorder p="md">
            <Stack gap="sm">
              <Text fw={600} size="sm" c="dimmed">
                PROCEDURE DESCRIPTION
              </Text>
              <Divider />
              <Text
                size="sm"
                c={procedure.description ? 'inherit' : 'dimmed'}
              >
                {procedure.description || 'No description available'}
              </Text>
            </Stack>
          </Card>

          {/* Complications Section */}
          <Card withBorder p="md">
            <Stack gap="sm">
              <Text fw={600} size="sm" c="dimmed">
                COMPLICATIONS
              </Text>
              <Divider />
              <Text
                size="sm"
                c={procedure.procedure_complications ? '#d63384' : 'dimmed'}
              >
                {procedure.procedure_complications || 'No complications reported'}
              </Text>
            </Stack>
          </Card>

          {/* Anesthesia Section */}
          <Card withBorder p="md">
            <Stack gap="sm">
              <Text fw={600} size="sm" c="dimmed">
                ANESTHESIA INFORMATION
              </Text>
              <Divider />
              <Stack gap="xs">
                <Group>
                  <Text size="sm" fw={500} w={100}>
                    Type:
                  </Text>
                  {procedure.anesthesia_type ? (
                    <Badge variant="light" color="purple" size="sm">
                      {procedure.anesthesia_type}
                    </Badge>
                  ) : (
                    <Text size="sm" c="dimmed">
                      Not specified
                    </Text>
                  )}
                </Group>
                <Group align="flex-start">
                  <Text size="sm" fw={500} w={100}>
                    Notes:
                  </Text>
                  <Text
                    size="sm"
                    style={{ flex: 1 }}
                    c={procedure.anesthesia_notes ? 'inherit' : 'dimmed'}
                  >
                    {procedure.anesthesia_notes || 'No anesthesia notes available'}
                  </Text>
                </Group>
              </Stack>
            </Stack>
          </Card>

          {/* Clinical Notes Section */}
          <Card withBorder p="md">
            <Stack gap="sm">
              <Text fw={600} size="sm" c="dimmed">
                CLINICAL NOTES
              </Text>
              <Divider />
              <Text
                size="sm"
                c={procedure.notes ? 'inherit' : 'dimmed'}
              >
                {procedure.notes || 'No clinical notes available'}
              </Text>
            </Stack>
          </Card>

          {/* Document Management */}
          <DocumentSection
            entityType="procedure"
            entityId={procedure.id}
            mode="view"
            onUploadComplete={handleDocumentUploadComplete}
            onError={handleDocumentError}
          />

          {/* Action Buttons */}
          <Group justify="flex-end" mt="md">
            <Button
              variant="filled"
              size="xs"
              onClick={handleEditClick}
            >
              Edit Procedure
            </Button>
            <Button variant="filled" onClick={onClose}>
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

export default ProcedureViewModal;