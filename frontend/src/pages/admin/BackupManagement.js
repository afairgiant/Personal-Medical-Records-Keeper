import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/admin/AdminLayout';
import AdminCard from '../../components/admin/AdminCard';
import { useAdminData } from '../../hooks/useAdminData';
import { useBackupNotifications } from '../../hooks/useBackupNotifications';
import { adminApiService } from '../../services/api/adminApi';
import { Loading } from '../../components';
import { formatDateTime } from '../../utils/helpers';
import './BackupManagement.css';

const BackupManagement = () => {
  const navigate = useNavigate();
  const [creating, setCreating] = useState({});
  const [restoring, setRestoring] = useState({});
  const [uploading, setUploading] = useState(false);
  const [showAdvancedMenu, setShowAdvancedMenu] = useState(false);

  // Enhanced notification system
  const { showSuccess, showError, showLoading, hideLoading, showWarning } = useBackupNotifications();

  // Backup Management with auto-refresh
  const {
    data: backupData,
    loading,
    error,
    refreshData,
    executeAction: rawExecuteAction,
  } = useAdminData({
    entityName: 'Backup Management',
    apiMethodsConfig: {
      load: signal => adminApiService.getBackups(signal),
      createDatabaseBackup: (description, signal) =>
        adminApiService.createDatabaseBackup(description, signal),
      createFilesBackup: (description, signal) =>
        adminApiService.createFilesBackup(description, signal),
      createFullBackup: (description, signal) =>
        adminApiService.createFullBackup(description, signal),
      uploadBackup: (file, signal) =>
        adminApiService.uploadBackup(file, signal),
      downloadBackup: (backupId, signal) =>
        adminApiService.downloadBackup(backupId, signal),
      verifyBackup: (backupId, signal) =>
        adminApiService.verifyBackup(backupId, signal),
      deleteBackup: (backupId, signal) =>
        adminApiService.deleteBackup(backupId, signal),
      cleanupBackups: signal => adminApiService.cleanupBackups(signal),
      cleanupAllOldData: signal => adminApiService.cleanupAllOldData(signal),
      restoreBackup: (data, signal) =>
        adminApiService.executeRestore(
          data.backupId,
          data.confirmationToken,
          signal
        ),
    },
  });

  // Wrap executeAction to suppress default success messages
  const executeAction = async (actionName, actionData = null) => {
    try {
      return await rawExecuteAction(actionName, actionData);
    } catch (error) {
      // Let our enhanced notification system handle the error
      throw error;
    }
  };

  const backups = backupData?.backups || [];

  const handleCreateBackup = async type => {
    setCreating(prev => ({ ...prev, [type]: true }));

    // Determine action name for notifications
    const actionName = type === 'database' ? 'createDatabaseBackup' 
                    : type === 'files' ? 'createFilesBackup' 
                    : 'createFullBackup';

    // Show loading notification for longer operations
    const loadingId = showLoading(actionName);

    try {
      const description = `Manual ${type} backup created on ${formatDateTime(new Date().toISOString())}`;

      let result;
      if (type === 'database') {
        result = await executeAction('createDatabaseBackup', description);
      } else if (type === 'files') {
        result = await executeAction('createFilesBackup', description);
      } else if (type === 'full') {
        result = await executeAction('createFullBackup', description);
      }

      // Hide loading notification and show success
      hideLoading(loadingId);
      if (result) {
        showSuccess(actionName, result);
        await refreshData();
      }
    } catch (error) {
      // Hide loading notification and show error
      hideLoading(loadingId);
      showError(actionName, error);
      console.error(`${actionName} failed:`, error);
    } finally {
      setCreating(prev => ({ ...prev, [type]: false }));
    }
  };

  const handleUploadBackup = async event => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const filename = file.name.toLowerCase();
    if (!filename.endsWith('.sql') && !filename.endsWith('.zip')) {
      showWarning('Invalid File Type', 'Please select a .sql or .zip backup file.');
      return;
    }

    setUploading(true);
    const loadingId = showLoading('uploadBackup');

    try {
      const result = await executeAction('uploadBackup', file);
      
      hideLoading(loadingId);
      if (result) {
        showSuccess('uploadBackup', result);
        await refreshData();
        event.target.value = '';
      }
    } catch (error) {
      hideLoading(loadingId);
      showError('uploadBackup', error);
      console.error('Upload backup failed:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadBackup = async (backupId, filename) => {
    const loadingId = showLoading('downloadBackup');
    
    try {
      const blob = await executeAction('downloadBackup', backupId);
      
      hideLoading(loadingId);
      if (blob) {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showSuccess('downloadBackup');
      }
    } catch (error) {
      hideLoading(loadingId);
      showError('downloadBackup', error);
      console.error('Download failed:', error);
    }
  };

  const handleVerifyBackup = async backupId => {
    const loadingId = showLoading('verifyBackup');
    
    try {
      const result = await executeAction('verifyBackup', backupId);
      
      hideLoading(loadingId);
      if (result) {
        showSuccess('verifyBackup', result);
        await refreshData();
      }
    } catch (error) {
      hideLoading(loadingId);
      showError('verifyBackup', error);
      console.error('Verify backup failed:', error);
    }
  };

  const handleDeleteBackup = async (backupId, filename) => {
    const confirmDelete = window.confirm(
      `Are you sure you want to delete backup "${filename}"?\n\nThis action cannot be undone.`
    );

    if (confirmDelete) {
      const loadingId = showLoading('deleteBackup');
      
      try {
        const result = await executeAction('deleteBackup', backupId);
        
        hideLoading(loadingId);
        if (result) {
          showSuccess('deleteBackup', result);
          await refreshData();
        }
      } catch (error) {
        hideLoading(loadingId);
        showError('deleteBackup', error);
        console.error('Delete backup failed:', error);
      }
    }
  };

  const handleCleanupBackups = async () => {
    const loadingId = showLoading('cleanupBackups');
    
    try {
      const result = await executeAction('cleanupBackups');
      
      hideLoading(loadingId);
      if (result) {
        showSuccess('cleanupBackups', result);
        await refreshData();
      }
    } catch (error) {
      hideLoading(loadingId);
      showError('cleanupBackups', error);
      console.error('Cleanup backups failed:', error);
    }
  };

  const handleCompleteCleanup = async () => {
    const confirmCleanup = window.confirm(
      `⚠️ WARNING: Complete Cleanup will permanently remove:\n\n` +
      `• Old backup files\n` +
      `• Orphaned files\n` +
      `• Trash files\n\n` +
      `This action cannot be undone. Are you sure you want to proceed?`
    );

    if (!confirmCleanup) {
      return;
    }

    const loadingId = showLoading('cleanupAllOldData');
    
    try {
      const result = await executeAction('cleanupAllOldData');
      
      hideLoading(loadingId);
      if (result) {
        showSuccess('cleanupAllOldData', result);
        await refreshData();
      }
    } catch (error) {
      hideLoading(loadingId);
      showError('cleanupAllOldData', error);
      console.error('Complete cleanup failed:', error);
    }
  };

  const handleRestoreBackup = async (backupId, backupType) => {
    const confirmRestore = window.confirm(
      `⚠️ WARNING: This will restore from backup and REPLACE current data!\n\nAre you absolutely sure?`
    );

    if (!confirmRestore) return;

    setRestoring(prev => ({ ...prev, [backupId]: true }));
    const loadingId = showLoading('restoreBackup');
    
    try {
      // Get confirmation token first
      const tokenResponse =
        await adminApiService.getConfirmationToken(backupId);

      const result = await executeAction('restoreBackup', {
        backupId,
        confirmationToken: tokenResponse.confirmation_token,
      });

      hideLoading(loadingId);
      if (result) {
        showSuccess('restoreBackup', result);
        await refreshData();
      }
    } catch (error) {
      hideLoading(loadingId);
      showError('restoreBackup', error);
      console.error('Restore failed:', error);
    } finally {
      setRestoring(prev => ({ ...prev, [backupId]: false }));
    }
  };

  const formatFileSize = bytes => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading && !backupData) {
    return (
      <AdminLayout>
        <div className="admin-page-loading">
          <Loading message="Loading backup management..." />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="backup-management">
        {/* Header */}
        <AdminCard className="backup-header-card">
          <div className="backup-page-header">
            <h1>💾 Backup Management</h1>
            <p>Create and manage system backups</p>
          </div>
        </AdminCard>

        {/* Note: Notifications are now handled by Mantine notification system */}

        {/* Main Backup Actions */}
        <AdminCard title="⚡ Backup Operations" className="backup-actions-card">
          <div className="main-backup-actions">
            <BackupActionCard
              title="Full System Backup"
              description="Create a complete backup (database + files) - Recommended"
              buttonText="Create Full Backup"
              buttonClass="full compact-btn"
              loading={creating.full}
              onClick={() => handleCreateBackup('full')}
            />

            <BackupActionCard
              title="Upload Backup"
              description="Upload an external backup file (.sql or .zip)"
              isUpload={true}
              uploading={uploading}
              onUpload={handleUploadBackup}
            />

            <div className="advanced-actions-menu">
              <h3>Advanced Options</h3>
              <div className="menu-trigger">
                <button 
                  className="dots-menu-btn" 
                  onClick={() => setShowAdvancedMenu(!showAdvancedMenu)}
                  aria-expanded={showAdvancedMenu}
                  aria-haspopup="menu"
                  aria-label="Advanced backup options menu"
                >
                  <span>⋮</span> More Options
                </button>
                {showAdvancedMenu && (
                  <div className="dropdown-menu" role="menu">
                    <button 
                      className="dropdown-item"
                      role="menuitem"
                      onClick={() => { handleCreateBackup('database'); setShowAdvancedMenu(false); }}
                      disabled={creating.database}
                      aria-disabled={creating.database}
                    >
                      {creating.database ? 'Creating...' : 'Database Only Backup'}
                    </button>
                    <button 
                      className="dropdown-item"
                      role="menuitem"
                      onClick={() => { handleCreateBackup('files'); setShowAdvancedMenu(false); }}
                      disabled={creating.files}
                      aria-disabled={creating.files}
                    >
                      {creating.files ? 'Creating...' : 'Files Only Backup'}
                    </button>
                    <hr className="dropdown-divider" />
                    <button 
                      className="dropdown-item"
                      role="menuitem"
                      onClick={() => { handleCleanupBackups(); setShowAdvancedMenu(false); }}
                      disabled={loading}
                      aria-disabled={loading}
                    >
                      {loading ? 'Cleaning...' : 'Cleanup Old Backups'}
                    </button>
                    <button 
                      className="dropdown-item"
                      role="menuitem"
                      onClick={() => { handleCompleteCleanup(); setShowAdvancedMenu(false); }}
                      disabled={loading}
                      aria-disabled={loading}
                    >
                      {loading ? 'Cleaning...' : 'Complete Cleanup'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </AdminCard>

        {/* Existing Backups */}
        <AdminCard
          title="📋 Existing Backups"
          loading={loading}
          error={error}
          actions={
            <button
              className="refresh-btn"
              onClick={refreshData}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          }
        >
          <BackupTable
            backups={backups}
            onDownload={handleDownloadBackup}
            onVerify={handleVerifyBackup}
            onDelete={handleDeleteBackup}
            onRestore={handleRestoreBackup}
            restoring={restoring}
            formatFileSize={formatFileSize}
          />
        </AdminCard>
      </div>
    </AdminLayout>
  );
};

// Reusable BackupActionCard Component
const BackupActionCard = ({
  title,
  description,
  buttonText,
  buttonClass,
  loading,
  onClick,
  isUpload = false,
  uploading = false,
  onUpload,
}) => (
  <div className="backup-action-card">
    <h3>{title}</h3>
    <p>{description}</p>
    {isUpload ? (
      <div className="upload-section">
        <input
          type="file"
          accept=".sql,.zip"
          onChange={onUpload}
          disabled={uploading}
          id="backup-upload"
          style={{ display: 'none' }}
        />
        <label
          htmlFor="backup-upload"
          className={`backup-btn upload ${uploading ? 'disabled' : ''}`}
        >
          {uploading ? 'Uploading...' : 'Choose Backup File'}
        </label>
      </div>
    ) : (
      <button
        className={`backup-btn ${buttonClass}`}
        onClick={onClick}
        disabled={loading}
      >
        {loading ? 'Processing...' : buttonText}
      </button>
    )}
  </div>
);

// Reusable BackupTable Component
const BackupTable = ({
  backups,
  onDownload,
  onVerify,
  onDelete,
  onRestore,
  restoring,
  formatFileSize,
}) => {
  if (backups.length === 0) {
    return (
      <div className="no-backups">
        <div className="no-backups-icon">📭</div>
        <p>No backups found</p>
      </div>
    );
  }

  return (
    <div className="backup-table">
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Filename</th>
            <th>Size</th>
            <th>Status</th>
            <th>Created</th>
            <th>File Exists</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {backups.map(backup => (
            <BackupTableRow
              key={backup.id}
              backup={backup}
              onDownload={onDownload}
              onVerify={onVerify}
              onDelete={onDelete}
              onRestore={onRestore}
              restoring={restoring[backup.id]}
              formatFileSize={formatFileSize}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Reusable BackupTableRow Component
const BackupTableRow = ({
  backup,
  onDownload,
  onVerify,
  onDelete,
  onRestore,
  restoring,
  formatFileSize,
}) => (
  <tr>
    <td>
      <span className={`backup-type ${backup.backup_type}`}>
        {backup.backup_type}
      </span>
    </td>
    <td>{backup.filename}</td>
    <td>{backup.size_bytes ? formatFileSize(backup.size_bytes) : 'Unknown'}</td>
    <td>
      <span className={`backup-status ${backup.status}`}>{backup.status}</span>
    </td>
    <td>{formatDateTime(backup.created_at)}</td>
    <td>
      <span className={`file-exists ${backup.file_exists ? 'yes' : 'no'}`}>
        {backup.file_exists ? 'Yes' : 'No'}
      </span>
    </td>
    <td>
      <div className="backup-actions-cell">
        {backup.file_exists && (
          <button
            className="action-btn download"
            onClick={() => onDownload(backup.id, backup.filename)}
            title="Download backup"
          >
            Download
          </button>
        )}
        <button
          className="action-btn verify"
          onClick={() => onVerify(backup.id)}
          title="Verify backup integrity"
        >
          Verify
        </button>
        <button
          className="action-btn delete"
          onClick={() => onDelete(backup.id, backup.filename)}
          title="Delete backup record and file"
        >
          Delete
        </button>
        {backup.file_exists && (
          <button
            className="action-btn restore"
            onClick={() => onRestore(backup.id, backup.backup_type)}
            disabled={restoring}
            title="Restore from this backup (DANGER: Replaces current data)"
          >
            {restoring ? 'Restoring...' : 'Restore'}
          </button>
        )}
      </div>
    </td>
  </tr>
);

export default BackupManagement;
