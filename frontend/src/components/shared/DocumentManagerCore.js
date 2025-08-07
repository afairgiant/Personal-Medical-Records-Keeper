import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';
import { apiService } from '../../services/api';
import { getPaperlessSettings } from '../../services/api/paperlessApi';
import logger from '../../services/logger';
import { 
  ERROR_MESSAGES, 
  SUCCESS_MESSAGES,
  getUserFriendlyError,
  enhancePaperlessError,
  formatErrorWithContext
} from '../../constants/errorMessages';

// Import configuration from upload progress hook
const UPLOAD_CONFIG = {
  PROGRESS_UPDATE_INTERVAL: 800,
  PROGRESS_SIMULATION_RATE: 15
};

// Performance optimization utility: Debounce function for progress updates
const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};

// Performance monitoring utility - module scope to avoid ESLint issues
let performanceMonitorInstance = null;

const createPerformanceMonitor = () => {
  if (!performanceMonitorInstance) {
    performanceMonitorInstance = {
      renderCount: 0,
      stateUpdateCount: 0,
      lastRenderTime: Date.now(),
      
      logRender: (componentName, reason) => {
        performanceMonitorInstance.renderCount++;
        const now = Date.now();
        const timeSinceLastRender = now - performanceMonitorInstance.lastRenderTime;
        
        // Performance monitoring: Reduced logging frequency to prevent log spam
        if (performanceMonitorInstance.renderCount <= 5) {
          // Log first 5 renders for debugging
          logger.info('performance_initial_render', {
            component: componentName,
            renderCount: performanceMonitorInstance.renderCount,
            timeSinceLastRender,
            reason,
          });
        } else if (timeSinceLastRender < 50 && performanceMonitorInstance.renderCount % 10 === 0) {
          // Log frequent renders as potential issues (throttled)
          logger.warn('performance_frequent_render', {
            component: componentName,
            renderCount: performanceMonitorInstance.renderCount,
            timeSinceLastRender,
            reason,
          });
        } else if (performanceMonitorInstance.renderCount % 100 === 0) {
          // Log every 100th render for monitoring (reduced frequency)
          logger.info('performance_render_milestone', {
            component: componentName,
            renderCount: performanceMonitorInstance.renderCount,
            timeSinceLastRender,
            reason,
          });
        }
        
        performanceMonitorInstance.lastRenderTime = now;
      },
      
      logStateUpdate: (updateType, newValue) => {
        performanceMonitorInstance.stateUpdateCount++;
        if (performanceMonitorInstance.stateUpdateCount % 10 === 0) {
          logger.info('performance_state_updates', {
            component: 'DocumentManagerCore',
            totalUpdates: performanceMonitorInstance.stateUpdateCount,
            updateType,
            hasValue: !!newValue,
          });
        }
      },
    };
  }
  return performanceMonitorInstance;
};

/**
 * DocumentManagerCore - Main coordination and state management hook
 * Handles all business logic, API calls, and state management for document operations
 */
const useDocumentManagerCore = ({
  entityType,
  entityId,
  mode = 'view',
  onFileCountChange,
  onError,
  onUploadComplete,
  showProgressModal = true,
  uploadState,
  updateFileProgress,
  startUpload,
  completeUpload,
  resetUpload,
}) => {
  // Performance monitoring: Track component renders (throttled in view mode)
  const performanceMonitor = createPerformanceMonitor();
  // PERFORMANCE FIX: Reduce logging frequency in view mode
  const now = Date.now();
  const shouldLogRender = mode !== 'view' || (now - (performanceMonitor.lastViewModeLog || 0)) > 5000;
  if (shouldLogRender) {
    performanceMonitor.logRender('DocumentManagerCore', `mode=${mode}, entityId=${entityId}`);
    if (mode === 'view') {
      performanceMonitor.lastViewModeLog = now;
    }
  }
  
  // State management
  const [files, setFiles] = useState([]);
  const [pendingFiles, setPendingFiles] = useState([]);
  const [filesToDelete, setFilesToDelete] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [syncStatus, setSyncStatus] = useState({});
  const [syncLoading, setSyncLoading] = useState(false);

  // Performance optimization: Enhanced state setters with monitoring
  const monitoredSetFiles = useCallback((newFiles) => {
    performanceMonitor.logStateUpdate('files', newFiles);
    setFiles(newFiles);
  }, []);
  
  const monitoredSetPendingFiles = useCallback((newPendingFiles) => {
    performanceMonitor.logStateUpdate('pendingFiles', newPendingFiles);
    setPendingFiles(newPendingFiles);
  }, []);

  // Paperless settings state
  const [paperlessSettings, setPaperlessSettings] = useState(null);
  const [selectedStorageBackend, setSelectedStorageBackend] = useState('local');
  const [paperlessLoading, setPaperlessLoading] = useState(true);

  // Performance optimization: Memoize expensive progress statistics
  const progressStats = useMemo(() => {
    if (!uploadState || !uploadState.files || uploadState.files.length === 0) {
      return { completed: 0, failed: 0, uploading: 0, total: 0 };
    }
    
    const completed = uploadState.files.filter(f => f.status === 'completed').length;
    const failed = uploadState.files.filter(f => f.status === 'failed').length;
    const uploading = uploadState.files.filter(f => f.status === 'uploading').length;
    const total = uploadState.files.length;
    
    return { completed, failed, uploading, total };
  }, [uploadState?.files]);

  // Performance optimization: Memoize file size calculations
  const fileStats = useMemo(() => {
    if (!files || files.length === 0) {
      return { totalSize: 0, averageSize: 0 };
    }
    
    const totalSize = files.reduce((sum, file) => sum + (file.size || 0), 0);
    const averageSize = totalSize / files.length;
    
    return { totalSize, averageSize };
  }, [files]);

  // Performance optimization: Memoize pending files stats
  const pendingStats = useMemo(() => {
    if (!pendingFiles || pendingFiles.length === 0) {
      return { count: 0, totalSize: 0 };
    }
    
    const count = pendingFiles.length;
    const totalSize = pendingFiles.reduce((sum, pf) => sum + (pf.file?.size || 0), 0);
    
    return { count, totalSize };
  }, [pendingFiles]);

  // Performance optimization: Debounced progress update function
  // Only create in upload modes to prevent unnecessary function creation in view mode
  const debouncedUpdateProgress = useMemo(() => {
    if (mode === 'view' && !uploadState?.isUploading) {
      // Return a no-op function in view mode when not uploading
      return () => {};
    }
    return debounce((fileId, progress, status, error) => {
      updateFileProgress(fileId, progress, status, error);
    }, 150); // Increased debounce for better performance
  }, [mode, uploadState?.isUploading, updateFileProgress]);

  // Rate limiting for logging
  const lastLogTimeRef = useRef(0);
  const LOG_THROTTLE_MS = 1000; // 1 second throttle

  // Refs for stable callbacks
  const filesRef = useRef(files);
  const pendingFilesRef = useRef(pendingFiles);
  const selectedStorageBackendRef = useRef(selectedStorageBackend);
  const paperlessSettingsRef = useRef(paperlessSettings);
  const paperlessAutoSyncRef = useRef(paperlessSettings?.paperless_auto_sync);
  
  // Ref to track progress intervals for proper cleanup
  const progressIntervalsRef = useRef(new Set());

  // Performance optimization: Batch ref updates to reduce effect executions
  useEffect(() => {
    filesRef.current = files;
    pendingFilesRef.current = pendingFiles;
    selectedStorageBackendRef.current = selectedStorageBackend;
    paperlessSettingsRef.current = paperlessSettings;
    paperlessAutoSyncRef.current = paperlessSettings?.paperless_auto_sync;
  }, [files, pendingFiles, selectedStorageBackend, paperlessSettings]);

  // Load paperless settings
  const loadPaperlessSettings = useCallback(async () => {
    setPaperlessLoading(true);
    try {
      const settings = await getPaperlessSettings();
      setPaperlessSettings(settings);

      // Paperless settings loaded successfully

      // Determine the storage backend to use
      if (settings?.default_storage_backend) {
        // User has explicitly set a default - always respect it
        setSelectedStorageBackend(settings.default_storage_backend);
      } else {
        // No default set - check if Paperless is fully configured
        if (settings?.paperless_enabled && 
            settings?.paperless_url && 
            settings?.paperless_has_credentials) {
          // Paperless is fully configured - use it as default for better UX
          setSelectedStorageBackend('paperless');
          logger.info('Auto-selected Paperless storage (no default set but Paperless configured)', {
            entityType,
            entityId,
            component: 'DocumentManagerCore',
          });
        } else {
          // Paperless not configured or incomplete - fallback to local
          setSelectedStorageBackend('local');
        }
      }

      logger.info('Paperless settings loaded successfully', {
        paperlessEnabled: settings?.paperless_enabled,
        hasUrl: !!settings?.paperless_url,
        hasCredentials: !!settings?.paperless_has_credentials,
        defaultBackend: settings?.default_storage_backend,
        entityType,
        entityId,
        component: 'DocumentManagerCore',
      });

      // Enhanced debugging for lab results specifically
      if (entityType === 'lab-result') {
        logger.info('LAB_RESULTS_PAPERLESS_DEBUG', {
          message: 'Lab Results Paperless settings debug',
          entityType,
          entityId,
          paperlessEnabled: settings?.paperless_enabled,
          hasUrl: !!settings?.paperless_url,
          hasCredentials: !!settings?.paperless_has_credentials,
          defaultBackend: settings?.default_storage_backend,
          willUsePaperless: settings?.default_storage_backend === 'paperless',
          component: 'DocumentManagerCore',
        });
      }
    } catch (err) {
      logger.warn('Failed to load paperless settings', {
        error: err.message,
        entityType,
        entityId,
        component: 'DocumentManagerCore',
      });
      setPaperlessSettings(null);
      setSelectedStorageBackend('local');
    } finally {
      setPaperlessLoading(false);
    }
  }, [entityType, entityId]);

  // Load files from server
  const loadFiles = useCallback(async () => {
    if (!entityId) return;

    setError('');

    try {
      const response = await apiService.getEntityFiles(entityType, entityId);
      const fileList = Array.isArray(response) ? response : [];
      
      // Files loaded successfully
      
      // Performance optimization: Prevent unnecessary re-renders with enhanced comparison
      monitoredSetFiles(prevFiles => {
        // Quick length check first (most common case)
        if (prevFiles.length !== fileList.length) {
          return fileList;
        }
        
        // Enhanced comparison checking both id and updated_at for better change detection
        const hasChanged = !prevFiles.every((file, index) => {
          const newFile = fileList[index];
          return newFile && file.id === newFile.id && file.updated_at === newFile.updated_at;
        });
        
        return hasChanged ? fileList : prevFiles;
      });

      if (onFileCountChange) {
        onFileCountChange(fileList.length);
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to load files';
      setError(errorMessage);

      if (onError) {
        onError(errorMessage);
      }

      logger.error('document_manager_load_error', {
        message: 'Failed to load files',
        entityType,
        entityId,
        error: err.message,
        component: 'DocumentManagerCore',
      });
    }
  }, [entityType, entityId, onFileCountChange, onError]);

  // Check sync status for Paperless documents
  // Performance optimization: Use stable references to prevent infinite loops
  const checkSyncStatus = useCallback(async (isManualSync = false) => {
    if (isManualSync) setSyncLoading(true);

    try {
      // Use current values from refs for stable dependencies
      const currentFiles = filesRef.current || files;
      const paperlessFiles = currentFiles.filter(f => f.storage_backend === 'paperless');
      
      // Check sync status for Paperless files
      
      // For manual sync, always try the API call even if frontend doesn't see paperless files
      // The backend might know about files that need sync checking
      if (paperlessFiles.length === 0 && !isManualSync) {
        // No Paperless files found, skipping automatic sync check
        logger.debug('No Paperless files found, skipping automatic sync check', {
          entityType,
          entityId,
          isManualSync,
          component: 'DocumentManagerCore',
        });
        return;
      }

      if (!paperlessSettings?.paperless_enabled) {
        logger.warn('paperless_not_enabled_sync_skip', 'Paperless not enabled, skipping sync check', {
          entityType,
          entityId,
          isManualSync,
          paperlessFilesCount: paperlessFiles.length,
          component: 'DocumentManagerCore',
        });
        
        if (isManualSync) {
          // Show notification for manual sync when paperless not enabled
          const { notifications } = await import('@mantine/notifications');
          const { IconExclamationMark } = await import('@tabler/icons-react');
          
          notifications.show({
            title: 'Sync Check Failed',
            message: 'Paperless integration is not enabled. Please enable it in Settings.',
            color: 'orange',
            icon: <IconExclamationMark size={16} />,
            autoClose: 5000,
          });
        }
        
        if (isManualSync) setSyncLoading(false);
        return;
      }
      
      logger.info('sync_status_check_start', 'Starting Paperless sync status check', {
        entityType,
        entityId,
        isManualSync,
        paperlessFilesCount: paperlessFiles.length,
        paperlessEnabled: paperlessSettings?.paperless_enabled,
        autoSyncEnabled: paperlessSettings?.paperless_auto_sync,
        component: 'DocumentManagerCore',
      });

      // First, update any processing files to check if tasks have completed
      try {
        logger.debug('processing_files_update_start', 'Updating processing files status', {
          entityType,
          entityId,
          component: 'DocumentManagerCore'
        });
        const processingUpdates = await apiService.updateProcessingFiles();
        if (Object.keys(processingUpdates).length > 0) {
          logger.info('processing_files_updated', 'Processing files updated', {
            entityType,
            entityId,
            updates: processingUpdates,
            component: 'DocumentManagerCore',
          });
        }
      } catch (processingError) {
        logger.warn('processing_files_update_failed', 'Failed to update processing files', {
          entityType,
          entityId,
          error: processingError.message,
          component: 'DocumentManagerCore',
        });
        // Continue with sync check even if processing update fails
      }

      const status = await apiService.checkPaperlessSyncStatus();
      setSyncStatus(status);
      
      // Count missing files for logging and user notification
      const missingCount = Object.values(status).filter(exists => !exists).length;
      const totalChecked = Object.keys(status).length;
      
      logger.info('Paperless sync status check completed', {
        entityType,
        entityId,
        isManualSync,
        totalFilesChecked: totalChecked,
        missingFilesFound: missingCount,
        syncStatus: status,
        component: 'DocumentManagerCore',
      });

      // Show notification for manual sync with results
      if (isManualSync) {
        const { notifications } = await import('@mantine/notifications');
        const { IconCheck, IconAlertTriangle } = await import('@tabler/icons-react');
        
        if (missingCount > 0) {
          notifications.show({
            title: 'Sync Check Complete',
            message: `Found ${missingCount} missing document(s) out of ${totalChecked} checked. Missing documents are marked with red strikethrough.`,
            color: 'yellow',
            icon: <IconAlertTriangle size={16} />,
            autoClose: 8000,
          });
        } else {
          notifications.show({
            title: 'Sync Check Complete',
            message: `All ${totalChecked} Paperless documents are synced and available.`,
            color: 'green',
            icon: <IconCheck size={16} />,
            autoClose: 5000,
          });
        }
      }
      
      // Reload files to refresh the UI with updated sync status
      await loadFiles();
    } catch (err) {
      const currentFiles = filesRef.current || files;
      const paperlessFiles = currentFiles.filter(f => f.storage_backend === 'paperless');
      
      logger.error('document_manager_sync_check_error', {
        message: 'Failed to check Paperless sync status',
        entityType,
        entityId,
        isManualSync,
        error: err.message,
        paperlessFilesCount: paperlessFiles.length,
        component: 'DocumentManagerCore',
      });

      // Show error notification for manual sync
      if (isManualSync) {
        const { notifications } = await import('@mantine/notifications');
        const { IconX } = await import('@tabler/icons-react');
        
        notifications.show({
          title: 'Sync Check Failed',
          message: `Failed to check Paperless sync status: ${err.message}. Please check your Paperless connection.`,
          color: 'red',
          icon: <IconX size={16} />,
          autoClose: 8000,
        });
      }
    } finally {
      if (isManualSync) setSyncLoading(false);
    }
  }, [entityType, entityId, loadFiles, paperlessSettings]);

  // Performance optimization: Split file loading effect from paperless settings
  // This prevents unnecessary file reloads when paperless settings change
  useEffect(() => {
    if (entityId && mode !== 'create') {
      setLoading(true);
      loadFiles().finally(() => {
        setLoading(false);
      });
    }
  }, [entityId, mode, loadFiles]);

  // Load paperless settings only once on mount
  useEffect(() => {
    loadPaperlessSettings();
  }, []);

  // Performance optimization: Memoize sync check to prevent infinite loops
  const memoizedCheckSyncStatus = useCallback(() => {
    const currentFiles = filesRef.current;
    const currentAutoSync = paperlessAutoSyncRef.current;
    
    const paperlessFiles = currentFiles.filter(f => f.storage_backend === 'paperless');
    const shouldAutoSync = currentAutoSync && paperlessFiles.length > 0;
    
    // Evaluate auto-sync conditions
    
    if (shouldAutoSync) {
      // Auto-sync triggering on component load
      
      logger.info('Auto-sync triggered on component load', {
        entityType,
        entityId,
        paperlessFilesCount: paperlessFiles.length,
        autoSyncEnabled: currentAutoSync,
        component: 'DocumentManagerCore',
      });
      
      checkSyncStatus();
    } else {
      logger.debug('auto_sync_not_triggered', 'Auto-sync not triggered', {
        reason: !currentAutoSync ? 'Auto-sync disabled' : 
                paperlessFiles.length === 0 ? 'No Paperless files' : 'Unknown',
        paperlessAutoSync: currentAutoSync,
        paperlessFileCount: paperlessFiles.length,
        component: 'DocumentManagerCore'
      });
    }
  }, [paperlessSettings?.paperless_enabled, checkSyncStatus, entityType, entityId]);

  // Run auto-sync check when files or settings change (debounced)
  // Performance optimization: Skip in view mode to prevent frequent triggers
  useEffect(() => {
    // PERFORMANCE FIX: Skip auto-sync checks in view mode
    if (mode === 'view') {
      return;
    }

    const timeoutId = setTimeout(() => {
      memoizedCheckSyncStatus();
    }, 500); // Debounce to prevent frequent sync checks
    
    return () => clearTimeout(timeoutId);
  }, [mode, memoizedCheckSyncStatus]);

  // Optional: Periodic sync checking every 5 minutes when auto-sync is enabled
  // Performance optimization: Only run in edit/create modes, skip in view mode
  const periodicSyncIntervalRef = useRef(null);
  
  useEffect(() => {
    // PERFORMANCE FIX: Skip periodic sync in view mode to prevent frequent renders
    if (mode === 'view') {
      if (periodicSyncIntervalRef.current) {
        clearInterval(periodicSyncIntervalRef.current);
        periodicSyncIntervalRef.current = null;
        logger.debug('Periodic auto-sync disabled in view mode', {
          entityType,
          entityId,
          component: 'DocumentManagerCore',
        });
      }
      return;
    }

    const hasPaperlessFiles = files.some(f => f.storage_backend === 'paperless');
    const shouldRunPeriodicSync = paperlessSettings?.paperless_auto_sync && hasPaperlessFiles;
    
    if (shouldRunPeriodicSync && !periodicSyncIntervalRef.current) {
      periodicSyncIntervalRef.current = setInterval(() => {
        logger.info('Periodic auto-sync check triggered', {
          entityType,
          entityId,
          component: 'DocumentManagerCore',
        });
        checkSyncStatus();
      }, 5 * 60 * 1000); // 5 minutes
    } else if (!shouldRunPeriodicSync && periodicSyncIntervalRef.current) {
      clearInterval(periodicSyncIntervalRef.current);
      periodicSyncIntervalRef.current = null;
      logger.debug('Periodic auto-sync interval cleared', {
        entityType,
        entityId,
        component: 'DocumentManagerCore',
      });
    }
    
    return () => {
      if (periodicSyncIntervalRef.current) {
        clearInterval(periodicSyncIntervalRef.current);
        periodicSyncIntervalRef.current = null;
      }
    };
  }, [mode, paperlessSettings?.paperless_auto_sync, files.length, checkSyncStatus, entityType, entityId]);

  // Add pending file for batch upload
  const handleAddPendingFile = useCallback((file, description = '') => {
    monitoredSetPendingFiles(prev => [...prev, { file, description, id: Date.now() }]);
  }, [monitoredSetPendingFiles]);

  // Remove pending file
  const handleRemovePendingFile = useCallback(fileId => {
    monitoredSetPendingFiles(prev => prev.filter(f => f.id !== fileId));
  }, [monitoredSetPendingFiles]);

  // Mark file for deletion
  const handleMarkFileForDeletion = useCallback(fileId => {
    setFilesToDelete(prev => [...prev, fileId]);
  }, []);

  // Unmark file for deletion
  const handleUnmarkFileForDeletion = useCallback(fileId => {
    setFilesToDelete(prev => prev.filter(id => id !== fileId));
  }, []);

  // Performance optimization: Memoize expensive event handlers
  const handleImmediateUpload = useCallback(async (file, description = '') => {
    if (!entityId) {
      setError('Cannot upload file: entity ID not provided');
      return;
    }

    const fileId = `single-${Date.now()}`;

    // Show progress modal for single file upload
    if (showProgressModal) {
      startUpload([{ 
        id: fileId, 
        name: file.name, 
        size: file.size, 
        description 
      }]);
    }

    // Performance optimization: Batch initial state updates
    setLoading(true);
    setError('');

    try {
      logger.info('document_manager_upload_attempt', {
        message: 'Attempting file upload with task monitoring',
        entityType,
        entityId,
        fileName: file.name,
        selectedStorageBackend,
        paperlessEnabled: paperlessSettings?.paperless_enabled,
        component: 'DocumentManagerCore',
      });

      // Enhanced debugging for lab results specifically
      if (entityType === 'lab-result') {
        logger.info('LAB_RESULTS_UPLOAD_DEBUG', {
          message: 'Lab Results upload attempt debug',
          entityType,
          entityId,
          fileName: file.name,
          selectedStorageBackend,
          paperlessSettings: paperlessSettings ? {
            paperless_enabled: paperlessSettings.paperless_enabled,
            has_url: !!paperlessSettings.paperless_url,
            has_credentials: !!paperlessSettings.paperless_has_credentials,
            default_storage_backend: paperlessSettings.default_storage_backend
          } : null,
          component: 'DocumentManagerCore',
        });

        // Warning if Paperless is configured but upload is going to local storage
        if (selectedStorageBackend === 'local' && 
            paperlessSettings?.paperless_enabled && 
            paperlessSettings?.paperless_url && 
            paperlessSettings?.paperless_has_credentials) {
          logger.warn('LAB_RESULTS_PAPERLESS_MISCONFIGURATION', {
            message: 'Lab Results: Paperless is configured but upload going to local storage',
            entityType,
            entityId,
            fileName: file.name,
            selectedStorageBackend,
            paperlessConfigured: true,
            recommendation: 'User should change storage backend to Paperless or update default in Settings',
            component: 'DocumentManagerCore',
          });

          // Show user-facing notification for this scenario
          if (!showProgressModal) {
            notifications.show({
              title: 'Storage Backend Notice',
              message: 'File uploading to local storage. Use the storage selector to send to Paperless if desired.',
              color: 'blue',
              autoClose: 8000,
            });
          }
        }
      }

      // Update initial progress
      if (showProgressModal) {
        updateFileProgress(fileId, 10, 'uploading', 'Uploading to server...');
      }

      // Use the new upload method with task monitoring
      const uploadResult = await apiService.uploadEntityFileWithTaskMonitoring(
        entityType,
        entityId,
        file,
        description,
        '',
        selectedStorageBackend,
        null, // signal
        (progressUpdate) => {
          // Handle progress updates during task monitoring
          if (showProgressModal) {
            let progress = 50; // Start at 50% after initial upload
            let status = 'uploading';
            let message = progressUpdate.message || 'Processing...';

            if (progressUpdate.status === 'processing') {
              progress = 75;
              status = 'uploading';
            } else if (progressUpdate.status === 'completed') {
              progress = 100;
              status = 'completed';
            } else if (progressUpdate.status === 'failed') {
              progress = 0;
              status = 'failed';
            }

            updateFileProgress(fileId, progress, status, message);
          }
        }
      );

      // Handle different upload outcomes
      if (uploadResult.taskMonitored && selectedStorageBackend === 'paperless') {
        // Import duplicate handling utilities
        const { handlePaperlessTaskCompletion } = await import('../../utils/errorMessageUtils');
        
        // Handle task completion with appropriate notifications
        const result = handlePaperlessTaskCompletion(
          uploadResult.taskResult, 
          file.name, 
          { skipNotification: showProgressModal }
        );

        if (showProgressModal) {
          if (result.success) {
            updateFileProgress(fileId, 100, 'completed');
            completeUpload(true, result.message);
          } else if (result.isDuplicate) {
            updateFileProgress(fileId, 0, 'failed', result.message);
            completeUpload(false, result.message);
          } else {
            updateFileProgress(fileId, 0, 'failed', result.message);
            completeUpload(false, result.message);
          }
        }

        // Log the result
        logger.info('document_manager_paperless_upload_result', {
          message: 'Paperless upload completed with task monitoring',
          entityType,
          entityId,
          fileName: file.name,
          success: result.success,
          isDuplicate: result.isDuplicate,
          documentId: result.documentId,
          component: 'DocumentManagerCore',
        });

        // If it's a duplicate, don't set error (it's expected behavior)
        if (!result.success && !result.isDuplicate) {
          setError(result.message);
          if (onError) {
            onError(result.message);
          }
        }
      } else {
        // Local storage or upload without task monitoring
        if (showProgressModal) {
          updateFileProgress(fileId, 100, 'completed');
          completeUpload(true, `${file.name} uploaded successfully!`);
        } else {
          notifications.show({
            title: 'File Uploaded',
            message: formatErrorWithContext(SUCCESS_MESSAGES.UPLOAD_SUCCESS, file.name),
            color: 'green',
            icon: <IconCheck size={16} />,
          });
        }

        logger.info('document_manager_local_upload_success', {
          message: 'File uploaded successfully to local storage',
          entityType,
          entityId,
          fileName: file.name,
          component: 'DocumentManagerCore',
        });
      }

      // Reload files to show updated state
      await loadFiles();

    } catch (err) {
      let errorMessage;

      // Enhance error messages for Paperless or use generic error handling
      if (selectedStorageBackend === 'paperless') {
        errorMessage = enhancePaperlessError(err.message || '');
      } else {
        errorMessage = getUserFriendlyError(err, 'upload');
      }
      
      // Add file context to the error message
      errorMessage = formatErrorWithContext(errorMessage, file.name);

      if (showProgressModal) {
        updateFileProgress(fileId, 0, 'failed', errorMessage);
        completeUpload(false, errorMessage);
      } else {
        notifications.show({
          title: 'Upload Failed',
          message: errorMessage,
          color: 'red',
          icon: <IconX size={16} />,
        });
      }

      setError(errorMessage);

      if (onError) {
        onError(errorMessage);
      }

      logger.error('document_manager_upload_error', {
        message: 'Failed to upload file',
        entityType,
        entityId,
        fileName: file.name,
        selectedStorageBackend,
        error: err.message,
        component: 'DocumentManagerCore',
      });
    } finally {
      setLoading(false);
    }
  }, [entityId, entityType, selectedStorageBackend, paperlessSettings, showProgressModal, startUpload, updateFileProgress, completeUpload, loadFiles, onError]);

  // Batch upload pending files with progress tracking
  const uploadPendingFiles = useCallback(async (targetEntityId = null) => {
    // Use the provided targetEntityId or fall back to the component's entityId
    const effectiveEntityId = targetEntityId || entityId;
    
    if (!effectiveEntityId) {
      logger.error('document_manager_upload_error', {
        message: 'Cannot upload files: no entity ID provided',
        entityType,
        component: 'DocumentManagerCore',
      });
      setError('Cannot upload files: no entity ID provided');
      return false;
    }
    
    const currentPendingFiles = pendingFilesRef.current;

    logger.info('document_manager_batch_upload_start', {
      message: 'Starting batch upload with progress tracking',
      entityType,
      targetEntityId: effectiveEntityId,
      pendingFilesCount: currentPendingFiles.length,
      component: 'DocumentManagerCore',
    });

    if (currentPendingFiles.length === 0) {
      return true;
    }

    // Start progress tracking
    if (showProgressModal) {
      const progressFiles = currentPendingFiles.map((pf, index) => ({
        id: `batch-${index}`,
        name: pf.file.name,
        size: pf.file.size,
        description: pf.description,
      }));
      startUpload(progressFiles);
    }

    const uploadPromises = currentPendingFiles.map(async (pendingFile, index) => {
      const fileId = `batch-${index}`;

      try {
        // Mark as starting
        if (showProgressModal) {
          debouncedUpdateProgress(fileId, 5, 'uploading');
        }

        const currentStorageBackend = selectedStorageBackendRef.current;
        const currentPaperlessSettings = paperlessSettingsRef.current;

        logger.info('document_manager_individual_batch_upload', {
          message: 'Starting individual file upload in batch',
          entityType,
          targetEntityId: effectiveEntityId,
          fileName: pendingFile.file.name,
          selectedStorageBackend: currentStorageBackend,
          component: 'DocumentManagerCore',
        });

        // Enhanced debugging for lab results specifically
        if (entityType === 'lab-result') {
          logger.info('LAB_RESULTS_BATCH_UPLOAD_DEBUG', {
            message: 'Lab Results batch upload debug',
            entityType,
            targetEntityId: effectiveEntityId,
            fileName: pendingFile.file.name,
            selectedStorageBackend: currentStorageBackend,
            paperlessSettings: currentPaperlessSettings ? {
              paperless_enabled: currentPaperlessSettings.paperless_enabled,
              has_url: !!currentPaperlessSettings.paperless_url,
              has_credentials: !!currentPaperlessSettings.paperless_has_credentials,
              default_storage_backend: currentPaperlessSettings.default_storage_backend
            } : null,
            component: 'DocumentManagerCore',
          });

          // Warning if Paperless is configured but upload is going to local storage
          if (currentStorageBackend === 'local' && 
              currentPaperlessSettings?.paperless_enabled && 
              currentPaperlessSettings?.paperless_url && 
              currentPaperlessSettings?.paperless_has_credentials) {
            logger.warn('LAB_RESULTS_BATCH_PAPERLESS_MISCONFIGURATION', {
              message: 'Lab Results Batch: Paperless is configured but upload going to local storage',
              entityType,
              targetEntityId: effectiveEntityId,
              fileName: pendingFile.file.name,
              selectedStorageBackend: currentStorageBackend,
              paperlessConfigured: true,
              recommendation: 'User should change storage backend to Paperless or update default in Settings',
              component: 'DocumentManagerCore',
            });
          }
        }

        // Simulate progress updates for better UX with proper interval tracking
        let progressInterval = null;
        if (showProgressModal && currentStorageBackend === 'paperless') {
          let currentProgress = 10;
          progressInterval = setInterval(() => {
            if (currentProgress < 85) {
              currentProgress += Math.random() * UPLOAD_CONFIG.PROGRESS_SIMULATION_RATE;
              debouncedUpdateProgress(fileId, Math.min(currentProgress, 85), 'uploading');
            }
          }, UPLOAD_CONFIG.PROGRESS_UPDATE_INTERVAL);
          
          // Track interval for cleanup
          progressIntervalsRef.current.add(progressInterval);
        }

        try {
          // Use the new upload method with task monitoring
          const uploadResult = await apiService.uploadEntityFileWithTaskMonitoring(
            entityType,
            effectiveEntityId,
            pendingFile.file,
            pendingFile.description,
            '',
            currentStorageBackend,
            null, // signal
            (progressUpdate) => {
              // Handle progress updates during task monitoring for batch uploads
              if (showProgressModal) {
                let progress = 50; // Start at 50% after initial upload
                if (progressUpdate.status === 'processing') {
                  progress = 75;
                } else if (progressUpdate.status === 'completed') {
                  progress = 100;
                } else if (progressUpdate.status === 'failed') {
                  progress = 0;
                }
                debouncedUpdateProgress(fileId, progress, 'uploading', progressUpdate.message);
              }
            }
          );

          // Clean up interval properly
          if (progressInterval) {
            clearInterval(progressInterval);
            progressIntervalsRef.current.delete(progressInterval);
          }

          // Handle different upload outcomes for batch uploads
          if (uploadResult.taskMonitored && currentStorageBackend === 'paperless') {
            // Import duplicate handling utilities
            const { handlePaperlessTaskCompletion } = await import('../../utils/errorMessageUtils');
            
            // Handle task completion with appropriate notifications (skip notification for batch)
            const result = handlePaperlessTaskCompletion(
              uploadResult.taskResult, 
              pendingFile.file.name, 
              { skipNotification: true }
            );

            if (result.success) {
              // Mark as completed
              if (showProgressModal) {
                updateFileProgress(fileId, 100, 'completed');
              }

              logger.info('document_manager_batch_paperless_success', {
                message: 'Individual Paperless file uploaded successfully in batch',
                entityType,
                targetEntityId: effectiveEntityId,
                fileName: pendingFile.file.name,
                documentId: result.documentId,
                component: 'DocumentManagerCore',
              });
            } else if (result.isDuplicate) {
              // Mark as failed but log as duplicate
              if (showProgressModal) {
                updateFileProgress(fileId, 0, 'failed', result.message);
              }

              logger.warn('document_manager_batch_paperless_duplicate', {
                message: 'Duplicate document detected in batch upload',
                entityType,
                targetEntityId: effectiveEntityId,
                fileName: pendingFile.file.name,
                component: 'DocumentManagerCore',
              });

              // Don't throw error for duplicates - they are expected and should not crash the batch
              // The file will be marked as failed in the progress modal which is appropriate UX
            } else {
              // Mark as failed
              if (showProgressModal) {
                updateFileProgress(fileId, 0, 'failed', result.message);
              }

              logger.error('document_manager_batch_paperless_error', {
                message: 'Individual Paperless file failed in batch upload',
                entityType,
                targetEntityId: effectiveEntityId,
                fileName: pendingFile.file.name,
                error: result.message,
                component: 'DocumentManagerCore',
              });

              // Don't throw - let Promise.allSettled handle all results gracefully
            }
          } else {
            // Local storage or upload without task monitoring
            if (showProgressModal) {
              updateFileProgress(fileId, 100, 'completed');
            }

            logger.info('document_manager_batch_local_success', {
              message: 'Individual file uploaded successfully in batch (local storage)',
              entityType,
              targetEntityId: effectiveEntityId,
              fileName: pendingFile.file.name,
              component: 'DocumentManagerCore',
            });
          }
        } catch (error) {
          // Clean up interval on error
          if (progressInterval) {
            clearInterval(progressInterval);
            progressIntervalsRef.current.delete(progressInterval);
          }
          throw error;
        }
      } catch (error) {
        let errorMessage;

        // Enhance error messages for Paperless or use generic error handling
        if (selectedStorageBackendRef.current === 'paperless') {
          errorMessage = enhancePaperlessError(error.message || '');
        } else {
          errorMessage = getUserFriendlyError(error, 'upload');
        }
        
        // Add file context to the error message
        errorMessage = formatErrorWithContext(errorMessage, pendingFile.file.name);

        // Mark as failed
        if (showProgressModal) {
          updateFileProgress(fileId, 0, 'failed', errorMessage);
        }

        logger.error('document_manager_individual_batch_error', {
          message: 'Individual file upload failed in batch',
          entityType,
          targetEntityId: effectiveEntityId,
          fileName: pendingFile.file.name,
          error: error.message,
          enhancedError: errorMessage,
          component: 'DocumentManagerCore',
        });

        // Don't throw - let Promise.allSettled handle all results gracefully
      }
    });

    try {
      await Promise.allSettled(uploadPromises);

      // Check actual results from progress tracking
      const completedCount = uploadState?.files?.filter(f => f.status === 'completed').length || 0;
      const failedCount = uploadState?.files?.filter(f => f.status === 'failed').length || 0;
      const allSuccessful = failedCount === 0 && completedCount === currentPendingFiles.length;

      if (showProgressModal) {
        if (allSuccessful) {
          completeUpload(true, `All ${currentPendingFiles.length} file(s) uploaded successfully!`);
        } else {
          completeUpload(false, `Upload completed: ${completedCount} succeeded, ${failedCount} failed.`);
        }
      }

      monitoredSetPendingFiles([]);

      // Refresh data
      await loadFiles();

      if (onUploadComplete) {
        onUploadComplete(allSuccessful, completedCount, failedCount);
      }

      logger.info('document_manager_batch_upload_complete', {
        message: allSuccessful ? 'Batch upload completed successfully' : 'Batch upload completed with mixed results',
        entityType,
        targetEntityId: effectiveEntityId,
        fileCount: currentPendingFiles.length,
        completedCount,
        failedCount,
        component: 'DocumentManagerCore',
      });

      return allSuccessful;
    } catch (error) {
      // This should rarely happen since we use Promise.allSettled, but handle unexpected errors
      logger.error('document_manager_batch_upload_unexpected_error', {
        message: 'Unexpected error during batch upload',
        entityType,
        targetEntityId: effectiveEntityId,
        error: error.message,
        component: 'DocumentManagerCore',
      });

      if (showProgressModal) {
        completeUpload(false, `Upload failed: ${error.message}`);
      }

      if (onUploadComplete) {
        onUploadComplete(false, 0, currentPendingFiles.length);
      }

      return false;
    }
  }, [
    entityType,
    entityId,
    showProgressModal,
    startUpload,
    updateFileProgress,
    completeUpload,
    uploadState?.files,
    loadFiles,
    onUploadComplete,
  ]);

  // Performance optimization: Memoize download handler
  const handleDownloadFile = useCallback(async (fileId, fileName) => {
    try {
      await apiService.downloadEntityFile(fileId, fileName);

      logger.info('document_manager_download_success', {
        message: 'File downloaded successfully',
        entityType,
        entityId,
        fileId,
        fileName,
        component: 'DocumentManagerCore',
      });
    } catch (err) {
      const errorMessage = getUserFriendlyError(err, 'download');
      setError(errorMessage);

      if (onError) {
        onError(errorMessage);
      }

      logger.error('document_manager_download_error', {
        message: 'Failed to download file',
        entityType,
        entityId,
        fileId,
        fileName,
        error: err.message,
        component: 'DocumentManagerCore',
      });
    }
  }, [entityType, entityId, onError]);

  // View file in new tab
  const handleViewFile = useCallback(async (fileId, fileName) => {
    try {
      await apiService.viewEntityFile(fileId, fileName);

      logger.info('document_manager_view_success', {
        message: 'File viewed successfully',
        entityType,
        entityId,
        fileId,
        fileName,
        component: 'DocumentManagerCore',
      });
    } catch (err) {
      const errorMessage = getUserFriendlyError(err, 'view');
      setError(errorMessage);

      if (onError) {
        onError(errorMessage);
      }

      logger.error('document_manager_view_error', {
        message: 'Failed to view file',
        entityType,
        entityId,
        fileId,
        fileName,
        error: err.message,
        component: 'DocumentManagerCore',
      });
    }
  }, [entityType, entityId, onError]);

  // Performance optimization: Memoize delete handler
  const handleImmediateDelete = useCallback(async fileId => {
    if (!window.confirm('Are you sure you want to delete this file?')) {
      return;
    }

    // Performance optimization: Batch state updates for delete operation
    setLoading(true);
    setError('');

    try {
      await apiService.deleteEntityFile(fileId);
      await loadFiles();

      notifications.show({
        title: 'File Deleted',
        message: SUCCESS_MESSAGES.FILE_DELETED,
        color: 'green',
        icon: <IconCheck size={16} />,
      });

      logger.info('document_manager_delete_success', {
        message: 'File deleted successfully',
        entityType,
        entityId,
        fileId,
        component: 'DocumentManagerCore',
      });
    } catch (err) {
      const errorMessage = getUserFriendlyError(err, 'delete');
      setError(errorMessage);

      if (onError) {
        onError(errorMessage);
      }

      logger.error('document_manager_delete_error', {
        message: 'Failed to delete file',
        entityType,
        entityId,
        fileId,
        error: err.message,
        component: 'DocumentManagerCore',
      });
    } finally {
      setLoading(false);
    }
  }, [entityType, entityId, loadFiles, onError]);

  // Performance optimization: Memoize pending file description change handler
  const handlePendingFileDescriptionChange = useCallback((fileId, description) => {
    monitoredSetPendingFiles(prev =>
      prev.map(f =>
        f.id === fileId ? { ...f, description } : f
      )
    );
  }, [monitoredSetPendingFiles]);

  // Performance optimization: Memoize sync check handler
  const handleCheckSyncStatus = useCallback(() => {
    checkSyncStatus(true);
  }, [checkSyncStatus]);

  // Cleanup function to clear all intervals on component unmount
  useEffect(() => {
    return () => {
      // Clear all tracked progress intervals
      progressIntervalsRef.current.forEach(interval => {
        clearInterval(interval);
      });
      progressIntervalsRef.current.clear();
      
      // Performance monitoring: Log final component stats
      logger.info('document_manager_cleanup', {
        message: 'Component unmounting with performance stats',
        intervalCount: progressIntervalsRef.current.size,
        totalRenders: performanceMonitorInstance?.renderCount || 0,
        totalStateUpdates: performanceMonitorInstance?.stateUpdateCount || 0,
        component: 'DocumentManagerCore',
      });
    };
  }, []);

  // Performance optimization: Memoize the handlers object to prevent unnecessary re-renders
  const handlers = useMemo(() => ({
    // State
    files,
    pendingFiles,
    filesToDelete,
    loading,
    error,
    setError,
    syncStatus,
    syncLoading,
    paperlessSettings,
    selectedStorageBackend,
    setSelectedStorageBackend,
    paperlessLoading,
    
    // Statistics
    progressStats,
    fileStats,
    pendingStats,
    
    // Handlers
    handleAddPendingFile,
    handleRemovePendingFile,
    handleMarkFileForDeletion,
    handleUnmarkFileForDeletion,
    handleImmediateUpload,
    uploadPendingFiles,
    handleDownloadFile,
    handleViewFile,
    handleImmediateDelete,
    handlePendingFileDescriptionChange,
    handleCheckSyncStatus,
    loadFiles,
    checkSyncStatus,
    
    // API
    getPendingFilesCount: () => pendingFilesRef.current.length,
    hasPendingFiles: () => pendingFilesRef.current.length > 0,
    clearPendingFiles: () => monitoredSetPendingFiles([]),
  }), [
    files,
    pendingFiles,
    filesToDelete,
    loading,
    error,
    syncStatus,
    syncLoading,
    paperlessSettings,
    selectedStorageBackend,
    paperlessLoading,
    progressStats,
    fileStats,
    pendingStats,
    handleAddPendingFile,
    handleRemovePendingFile,
    handleMarkFileForDeletion,
    handleUnmarkFileForDeletion,
    handleImmediateUpload,
    uploadPendingFiles,
    handleDownloadFile,
    handleViewFile,
    handleImmediateDelete,
    handlePendingFileDescriptionChange,
    handleCheckSyncStatus,
    loadFiles,
    checkSyncStatus,
    monitoredSetPendingFiles,
  ]);

  // Return handlers object
  return handlers;
};

export default useDocumentManagerCore;