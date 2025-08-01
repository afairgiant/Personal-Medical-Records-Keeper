import React, { useState, useEffect } from 'react';
import {
  Modal,
  Stack,
  Group,
  Text,
  TextInput,
  Textarea,
  Button,
  Alert,
  ThemeIcon,
  Divider,
  Title,
  Paper,
  Badge,
  ActionIcon,
  Tooltip,
  Loader,
  Checkbox,
  Select,
} from '@mantine/core';
import {
  IconInfoCircle,
  IconUsers,
  IconTrash,
  IconMessageCircle,
  IconSend,
  IconMail,
  IconCheck,
  IconX,
  IconSend2,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import familyHistoryApi from '../../services/api/familyHistoryApi';
import { formatDateTime } from '../../utils/helpers';
import logger from '../../services/logger';
import {
  useErrorHandler,
  useErrorQueue,
  ErrorAlert,
  ErrorQueueAlert,
} from '../../utils/errorHandling';

const FamilyHistorySharingModal = ({
  opened,
  onClose,
  familyMember,
  familyMembers = [], // For bulk sharing
  onSuccess,
  bulkMode = false,
  enableErrorQueue = false, // New prop to enable error queue system (addresses reviewer feedback)
}) => {
  const [shares, setShares] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sharesLoading, setSharesLoading] = useState(false);
  const [shareForm, setShareForm] = useState({
    shared_with_identifier: '',
    sharing_note: '',
    expires_hours: 168, // Default to 7 days
  });
  const [selectedMembers, setSelectedMembers] = useState([]);

  // Always call both hooks to satisfy React rules, but only use one (addresses reviewer feedback)
  const queueSystem = useErrorQueue('FamilyHistorySharingModal');
  const singleSystem = useErrorHandler('FamilyHistorySharingModal');

  // Choose which system to use based on prop
  const {
    handleError,
    currentError,
    errorQueue = [],
    clearError,
    clearAllErrors,
    removeFromQueue,
  } = enableErrorQueue
    ? queueSystem
    : {
        ...singleSystem,
        errorQueue: [],
        clearAllErrors: singleSystem.clearError,
        removeFromQueue: () => {},
      };

  useEffect(() => {
    if (opened) {
      // Clear any previous error state when modal opens
      if (enableErrorQueue && clearAllErrors) {
        clearAllErrors();
      } else {
        clearError();
      }

      if (bulkMode) {
        // Initialize with all family members selected
        setSelectedMembers(familyMembers.map(member => member.id));
      } else if (familyMember) {
        loadShares();
      }
    }
  }, [opened, familyMember, bulkMode, familyMembers]);

  const loadShares = async () => {
    if (!familyMember) return;

    try {
      setSharesLoading(true);
      const shareData = await familyHistoryApi.getFamilyMemberShares(
        familyMember.id
      );
      setShares(shareData);
    } catch (error) {
      logger.error('Failed to load family member shares', {
        component: 'FamilyHistorySharingModal',
        familyMemberId: familyMember?.id,
        error: error.message,
      });
      notifications.show({
        title: 'Error',
        message: 'Failed to load sharing information',
        color: 'red',
        icon: <IconX size="1rem" />,
      });
    } finally {
      setSharesLoading(false);
    }
  };

  // The error handling is now managed by the useErrorHandler hook

  const sendInvitation = async () => {
    if (!shareForm.shared_with_identifier.trim()) {
      notifications.show({
        title: 'Error',
        message: 'Please enter a username or email',
        color: 'red',
        icon: <IconX size="1rem" />,
      });
      return;
    }

    try {
      setLoading(true);

      if (bulkMode) {
        // Bulk send invitations
        const result = await familyHistoryApi.bulkSendInvitations({
          family_member_ids: selectedMembers,
          shared_with_identifier: shareForm.shared_with_identifier,
          permission_level: 'view',
          sharing_note: shareForm.sharing_note,
          expires_hours: shareForm.expires_hours,
        });

        logger.debug('Bulk invitation results received', {
          component: 'FamilyHistorySharingModal',
          totalSent: result.total_sent,
          totalFailed: result.total_failed,
          selectedMemberCount: selectedMembers.length,
          hasRecipient: !!shareForm.shared_with_identifier,
          recipientType: shareForm.shared_with_identifier?.includes('@')
            ? 'email'
            : 'username',
          hasNote: !!shareForm.sharing_note,
          expiresHours: shareForm.expires_hours,
        });

        const successCount = result.total_sent;
        const failedCount = result.total_failed;

        if (successCount > 0) {
          notifications.show({
            title: 'Invitations Sent',
            message: `Successfully sent ${successCount} invitation(s)${failedCount > 0 ? `, ${failedCount} failed` : ''}`,
            color: 'green',
            icon: <IconCheck size="1rem" />,
          });
        }

        if (failedCount > 0) {
          notifications.show({
            title: 'Some Failed',
            message: `${failedCount} invitation(s) failed to send`,
            color: 'orange',
            icon: <IconX size="1rem" />,
          });
        }
      } else {
        // Single invitation
        await familyHistoryApi.sendShareInvitation(familyMember.id, {
          shared_with_identifier: shareForm.shared_with_identifier,
          permission_level: 'view',
          sharing_note: shareForm.sharing_note,
          expires_hours: shareForm.expires_hours,
        });

        notifications.show({
          title: 'Invitation Sent',
          message: `Invitation sent to share ${familyMember.name}'s family history`,
          color: 'green',
          icon: <IconCheck size="1rem" />,
        });

        await loadShares();
      }

      setShareForm({
        shared_with_identifier: '',
        sharing_note: '',
        expires_hours: 168,
      });
      if (onSuccess) onSuccess();
    } catch (error) {
      // Use the new error handling system with context
      handleError(error, {
        bulkMode,
        selectedMembers,
        familyMember,
        familyMembers,
        action: 'sending_invitation',
      });
    } finally {
      setLoading(false);
    }
  };

  const revokeShare = async share => {
    try {
      await familyHistoryApi.revokeShare(familyMember.id, share.shared_with.id);
      notifications.show({
        title: 'Access Revoked',
        message: 'Family history sharing has been revoked',
        color: 'orange',
        icon: <IconTrash size="1rem" />,
      });
      await loadShares();
      if (onSuccess) onSuccess();
    } catch (error) {
      handleError(error, {
        action: 'revoking_share',
        familyMember,
        shareId: share.id,
      });
    }
  };

  const handleClose = () => {
    setShareForm({
      shared_with_identifier: '',
      sharing_note: '',
      expires_hours: 168,
    });
    setSelectedMembers([]);
    // Clear error state based on system type
    if (enableErrorQueue && clearAllErrors) {
      clearAllErrors();
    } else {
      clearError();
    }
    onClose();
  };

  const handleFormChange = (field, value) => {
    setShareForm(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when user changes recipient
    if (
      field === 'shared_with_identifier' &&
      (currentError || errorQueue.length > 0)
    ) {
      if (enableErrorQueue && clearAllErrors) {
        clearAllErrors();
      } else {
        clearError();
      }
    }
  };

  const handleMemberToggle = memberId => {
    setSelectedMembers(current =>
      current.includes(memberId)
        ? current.filter(id => id !== memberId)
        : [...current, memberId]
    );
  };

  const handleSelectAll = () => {
    if (selectedMembers.length === familyMembers.length) {
      setSelectedMembers([]);
    } else {
      setSelectedMembers(familyMembers.map(member => member.id));
    }
  };

  const getTitle = () => {
    if (bulkMode) {
      return `Share Multiple Family Members (${selectedMembers.length} selected)`;
    }
    return familyMember
      ? `Share ${familyMember.name}'s Family History`
      : 'Share Family History';
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={getTitle()}
      size="lg"
      centered
      zIndex={2000}
      withinPortal
    >
      <Stack gap="md">
        <Alert icon={<IconInfoCircle />} color="blue" variant="light">
          <Text size="sm">
            {bulkMode
              ? "Share selected family members' medical history with another user. This only shares family history data, not your personal medical records."
              : `Share ${familyMember?.name}'s family medical history with another user. This only shares family history data, not your personal medical records.`}
          </Text>
        </Alert>

        {/* Family Member Selection (Bulk Mode) */}
        {bulkMode && (
          <Paper p="md" withBorder>
            <Group justify="space-between" mb="sm">
              <Text fw={500}>Select Family Members</Text>
              <Button variant="subtle" size="xs" onClick={handleSelectAll}>
                {selectedMembers.length === familyMembers.length
                  ? 'Deselect All'
                  : 'Select All'}
              </Button>
            </Group>
            <Stack gap="xs">
              {familyMembers.map(member => (
                <Checkbox
                  key={member.id}
                  checked={selectedMembers.includes(member.id)}
                  onChange={() => handleMemberToggle(member.id)}
                  label={
                    <Group gap="xs">
                      <Text>{member.name}</Text>
                      <Badge size="sm" variant="light">
                        {member.relationship}
                      </Badge>
                    </Group>
                  }
                />
              ))}
            </Stack>
          </Paper>
        )}

        {/* Single Family Member Info */}
        {!bulkMode && familyMember && (
          <Group gap="sm">
            <ThemeIcon color="blue" variant="light">
              <IconUsers />
            </ThemeIcon>
            <div>
              <Text fw={500}>{familyMember.name}</Text>
              <Text size="sm" c="dimmed">
                {familyMember.relationship}
              </Text>
            </div>
          </Group>
        )}

        <Divider />

        {/* Sharing Form */}
        <Stack gap="md">
          {/* Error display - supports both single error and error queue (addresses reviewer feedback) */}
          {enableErrorQueue ? (
            <ErrorQueueAlert
              errorQueue={errorQueue}
              onDismiss={removeFromQueue}
              onClearAll={clearAllErrors}
            />
          ) : (
            <ErrorAlert error={currentError} onClose={clearError} />
          )}

          <TextInput
            label="Share with (username or email)"
            placeholder="Enter username or email"
            value={shareForm.shared_with_identifier}
            onChange={e =>
              handleFormChange('shared_with_identifier', e.target.value)
            }
            required
            leftSection={<IconMail size="1rem" />}
            error={currentError && currentError.severity === 'high'}
          />

          <Textarea
            label="Note (optional)"
            placeholder="Add a note about why you're sharing this..."
            value={shareForm.sharing_note}
            onChange={e => handleFormChange('sharing_note', e.target.value)}
            rows={3}
            leftSection={<IconMessageCircle size="1rem" />}
          />

          <Select
            label="Invitation Expiration"
            placeholder="Select expiration time"
            value={
              shareForm.expires_hours === null
                ? 'never'
                : shareForm.expires_hours?.toString()
            }
            onChange={value =>
              handleFormChange(
                'expires_hours',
                value === 'never' ? null : parseInt(value)
              )
            }
            data={[
              { value: '24', label: '1 Day' },
              { value: '72', label: '3 Days' },
              { value: '168', label: '1 Week' },
              { value: '336', label: '2 Weeks' },
              { value: '720', label: '1 Month' },
              { value: 'never', label: 'Never Expires' },
            ]}
            description="How long the recipient has to accept the invitation"
          />

          <Button
            onClick={sendInvitation}
            loading={loading}
            disabled={
              !shareForm.shared_with_identifier.trim() ||
              (bulkMode && selectedMembers.length === 0)
            }
            leftSection={
              bulkMode ? <IconSend2 size="1rem" /> : <IconSend size="1rem" />
            }
            fullWidth
          >
            {bulkMode
              ? `Send ${selectedMembers.length} Invitation(s) (View Only)`
              : 'Send Invitation (View Only)'}
          </Button>
        </Stack>

        {/* Current Shares (Single Mode Only) */}
        {!bulkMode && (
          <>
            <Divider />
            {sharesLoading ? (
              <Group justify="center" py="md">
                <Loader size="sm" />
                <Text size="sm" c="dimmed">
                  Loading sharing information...
                </Text>
              </Group>
            ) : shares.length > 0 ? (
              <Stack gap="md">
                <Title order={4}>Currently Shared With:</Title>
                <Stack gap="xs">
                  {shares.map((share, index) => (
                    <Paper key={index} p="sm" withBorder>
                      <Group justify="space-between">
                        <div>
                          <Text fw={500}>{share.shared_with.name}</Text>
                          <Text size="sm" c="dimmed">
                            {share.shared_with.email}
                          </Text>
                          <Text size="xs" c="dimmed">
                            Shared on {formatDateTime(share.created_at)}
                          </Text>
                          {share.sharing_note && (
                            <Text size="xs" c="dimmed" italic>
                              <IconMessageCircle
                                size="0.8rem"
                                style={{ marginRight: 4 }}
                              />
                              "{share.sharing_note}"
                            </Text>
                          )}
                        </div>
                        <Group gap="xs">
                          <Badge size="sm" variant="light">
                            {share.permission_level || 'view'}
                          </Badge>
                          <Tooltip label="Revoke access">
                            <ActionIcon
                              color="red"
                              variant="subtle"
                              onClick={() => revokeShare(share)}
                            >
                              <IconTrash size="1rem" />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </Stack>
            ) : (
              <Paper p="md" radius="md" bg="gray.2">
                <Text size="sm" c="dimmed" ta="center">
                  This family history is not currently shared with anyone.
                </Text>
              </Paper>
            )}
          </>
        )}

        {/* Footer */}
        <Alert icon={<IconInfoCircle />} color="blue" variant="light">
          <Text size="xs">
            Recipients will receive an invitation that they can accept or
            reject. Only accepted invitations will grant access to the family
            history.
          </Text>
        </Alert>
      </Stack>
    </Modal>
  );
};

export default FamilyHistorySharingModal;
