import React, { memo } from 'react';
import {
  Stack,
  Paper,
  Title,
  Text,
  Group,
  Button,
  Center,
  Loader,
  ActionIcon,
  ThemeIcon,
  TextInput,
  Badge,
} from '@mantine/core';
import {
  IconUpload,
  IconRefresh,
  IconX,
  IconFileText,
  IconCheck,
} from '@tabler/icons-react';
import FileList from './FileList';
import FileUploadZone from './FileUploadZone';
import StorageBackendSelector from './StorageBackendSelector';

/**
 * Performance optimization: Extracted render logic into separate memoized component
 * This reduces the main component size and prevents unnecessary re-renders of the UI
 * when only internal state changes (like progress tracking) occur.
 */
const RenderModeContent = memo(({
  mode,
  loading,
  files,
  paperlessLoading,
  selectedStorageBackend,
  onStorageBackendChange,
  paperlessSettings,
  syncStatus,
  syncLoading,
  pendingFiles,
  filesToDelete,
  config,
  onUploadModalOpen,
  onCheckSyncStatus,
  onDownloadFile,
  onViewFile,
  onImmediateDelete,
  onMarkFileForDeletion,
  onUnmarkFileForDeletion,
  onAddPendingFile,
  onRemovePendingFile,
  onPendingFileDescriptionChange,
  onUploadPendingFiles,
}) => {
  // Performance optimization: Early return for loading state
  if (loading && files.length === 0) {
    return (
      <Center py="xl">
        <Stack align="center" gap="md">
          <Loader size="lg" />
          <Text>Loading files...</Text>
        </Stack>
      </Center>
    );
  }

  // Performance optimization: Memoized storage backend selector with auto-sync indicator
  const storageBackendSelector = !paperlessLoading && (
    <Stack gap="xs">
      <StorageBackendSelector
        value={selectedStorageBackend}
        onChange={onStorageBackendChange}
        paperlessEnabled={paperlessSettings?.paperless_enabled || false}
        paperlessConnected={
          paperlessSettings?.paperless_enabled &&
          paperlessSettings?.paperless_url &&
          paperlessSettings?.paperless_has_credentials
        }
        disabled={loading}
        size="sm"
      />
      {paperlessSettings?.paperless_auto_sync && (
        <Badge 
          size="xs" 
          color="green" 
          variant="light"
          leftSection={<IconCheck size={10} />}
        >
          Auto-sync enabled
        </Badge>
      )}
    </Stack>
  );

  // Performance optimization: Memoized pending files list
  const pendingFilesList = pendingFiles.length > 0 && (
    <Stack gap="md">
      <Title order={5}>Files to Upload:</Title>
      <Stack gap="sm">
        {pendingFiles.map(pendingFile => (
          <Paper key={pendingFile.id} withBorder p="sm" bg="blue.1">
            <Group justify="space-between" align="flex-start">
              <Group gap="xs" style={{ flex: 1 }}>
                <ThemeIcon variant="light" color="blue" size="sm">
                  <IconFileText size={14} />
                </ThemeIcon>
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Group gap="md">
                    <Text fw={500} size="sm">
                      {pendingFile.file.name}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {(pendingFile.file.size / 1024).toFixed(1)} KB
                    </Text>
                  </Group>
                  {mode === 'edit' && (
                    <TextInput
                      placeholder="Description (optional)"
                      value={pendingFile.description}
                      onChange={e => onPendingFileDescriptionChange(pendingFile.id, e.target.value)}
                      size="xs"
                    />
                  )}
                </Stack>
              </Group>
              <ActionIcon
                variant="light"
                color="red"
                size="sm"
                onClick={() => onRemovePendingFile(pendingFile.id)}
              >
                <IconX size={14} />
              </ActionIcon>
            </Group>
          </Paper>
        ))}
      </Stack>
      <Button
        leftSection={<IconUpload size={16} />}
        onClick={(e) => {
          e.preventDefault();
          onUploadPendingFiles();
        }}
        disabled={loading}
        size="sm"
      >
        Upload {pendingFiles.length} File{pendingFiles.length !== 1 ? 's' : ''}
      </Button>
    </Stack>
  );

  if (mode === 'view') {
    const hasPaperlessFiles = files.some(f => f.storage_backend === 'paperless');
    
    return (
      <Stack gap="md">
        {storageBackendSelector}
        
        {/* File Upload Section */}
        <Paper withBorder p="md" bg="gray.1">
          <Group justify="space-between" align="center">
            <Text fw={500}>Upload New File</Text>
            <Button
              leftSection={<IconUpload size={16} />}
              onClick={onUploadModalOpen}
              disabled={loading}
            >
              Upload File
            </Button>
          </Group>
        </Paper>

        {/* Files List with Sync Check for Paperless files */}
        {hasPaperlessFiles && (
          <Group justify="space-between" align="center">
            <Text fw={500}>Files</Text>
            <Button
              variant="light"
              size="xs"
              leftSection={<IconRefresh size={14} />}
              loading={syncLoading}
              onClick={onCheckSyncStatus}
              title="Check sync status with Paperless"
            >
              Sync Check
            </Button>
          </Group>
        )}
        
        <FileList
          files={files}
          syncStatus={syncStatus}
          showActions={true}
          onDownload={onDownloadFile}
          onView={onViewFile}
          onDelete={onImmediateDelete}
        />
      </Stack>
    );
  }

  if (mode === 'edit') {
    const hasPaperlessFiles = files.some(f => f.storage_backend === 'paperless');
    
    return (
      <Stack gap="md">
        {storageBackendSelector}

        {/* Existing Files */}
        {files.length > 0 && (
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Title order={5}>Current Files:</Title>
              {hasPaperlessFiles && (
                <Button
                  variant="light"
                  size="xs"
                  leftSection={<IconRefresh size={14} />}
                  loading={syncLoading}
                  onClick={onCheckSyncStatus}
                  title="Check sync status with Paperless"
                >
                  Sync Check
                </Button>
              )}
            </Group>
            <FileList
              files={files}
              filesToDelete={filesToDelete}
              syncStatus={syncStatus}
              showActions={true}
              onDownload={onDownloadFile}
              onView={onViewFile}
              onDelete={onMarkFileForDeletion}
              onRestore={onUnmarkFileForDeletion}
            />
          </Stack>
        )}

        {/* Add New Files */}
        <FileUploadZone
          onUpload={uploadedFiles => {
            uploadedFiles.forEach(({ file, description }) => {
              onAddPendingFile(file, description);
            });
          }}
          acceptedTypes={config.acceptedTypes}
          maxSize={config.maxSize}
          maxFiles={config.maxFiles}
          selectedStorageBackend={selectedStorageBackend}
          paperlessSettings={paperlessSettings}
        />

        {pendingFilesList}
      </Stack>
    );
  }

  if (mode === 'create') {
    return (
      <Stack gap="md">
        {storageBackendSelector}

        <FileUploadZone
          onUpload={uploadedFiles => {
            uploadedFiles.forEach(({ file, description }) => {
              onAddPendingFile(file, description);
            });
          }}
          acceptedTypes={config.acceptedTypes}
          maxSize={config.maxSize}
          maxFiles={config.maxFiles}
          autoUpload={true}
          selectedStorageBackend={selectedStorageBackend}
          paperlessSettings={paperlessSettings}
        />

        {pendingFilesList}
      </Stack>
    );
  }

  return null;
});

RenderModeContent.displayName = 'RenderModeContent';

export default RenderModeContent;