import logger from '../logger';
import { ENTITY_TYPES } from '../../utils/entityRelationships';

// Map entity types to their API endpoint paths
const ENTITY_TO_API_PATH = {
  [ENTITY_TYPES.MEDICATION]: 'medications',
  [ENTITY_TYPES.LAB_RESULT]: 'lab-results',
  [ENTITY_TYPES.IMMUNIZATION]: 'immunizations',
  [ENTITY_TYPES.INSURANCE]: 'insurances',
  [ENTITY_TYPES.PROCEDURE]: 'procedures',
  [ENTITY_TYPES.ALLERGY]: 'allergies',
  [ENTITY_TYPES.CONDITION]: 'conditions',
  [ENTITY_TYPES.TREATMENT]: 'treatments',
  [ENTITY_TYPES.ENCOUNTER]: 'encounters',
  [ENTITY_TYPES.VITALS]: 'vitals',
  [ENTITY_TYPES.PRACTITIONER]: 'practitioners',
  [ENTITY_TYPES.PHARMACY]: 'pharmacies',
  [ENTITY_TYPES.EMERGENCY_CONTACT]: 'emergency-contacts',
  [ENTITY_TYPES.PATIENT]: 'patients',
  [ENTITY_TYPES.FAMILY_MEMBER]: 'family-members',
};

// Streamlined API service with proper logging integration
class ApiService {
  constructor() {
    // Use environment variable for configurable API URL
    // Docker and production set REACT_APP_API_URL=/api/v1 for relative paths
    // Development uses REACT_APP_API_URL=http://localhost:8000/api/v1
    this.baseURL = process.env.REACT_APP_API_URL || '/api/v1';
    // Fallback URLs for better Docker compatibility
    this.fallbackURL = '/api/v1';
  }

  getAuthHeaders() {
    const token = localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };

    if (token) {
      try {
        // Validate token format before parsing
        if (typeof token !== 'string' || token.trim() === '') {
          throw new Error('Token is empty or not a string');
        }

        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
          throw new Error(`Invalid JWT format - expected 3 parts, got ${tokenParts.length}`);
        }

        // Check if token is expired
        const payload = JSON.parse(atob(tokenParts[1]));
        
        // Validate required JWT claims
        if (!payload.sub) {
          throw new Error('Token missing subject claim');
        }
        if (!payload.exp) {
          throw new Error('Token missing expiration claim');
        }

        const currentTime = Date.now() / 1000;
        if (payload.exp < currentTime) {
          logger.warn('Token expired, removing from storage');
          localStorage.removeItem('token');
          return headers;
        }

        headers['Authorization'] = `Bearer ${token}`;
      } catch (e) {
        logger.error('Invalid token format', { error: e.message });
        localStorage.removeItem('token');
      }
    }

    return headers;
  }
  async handleResponse(response, method, url) {
    if (!response.ok) {
      const errorData = await response.text();
      let errorMessage;
      let fullErrorData;

      try {
        fullErrorData = JSON.parse(errorData);
        errorMessage =
          fullErrorData.detail || fullErrorData.message || errorData; // For 422 errors, log the full validation details
        if (response.status === 422) {
          console.error('Validation Error Details:', fullErrorData);
          if (fullErrorData.detail && Array.isArray(fullErrorData.detail)) {
            const validationErrors = fullErrorData.detail
              .map(err => `${err.loc?.join('.')} - ${err.msg}`)
              .join('; ');
            errorMessage = `Validation Error: ${validationErrors}`;
          }
        }
      } catch {
        errorMessage =
          errorData ||
          `HTTP error! status: ${response.status} - ${response.statusText}`;
      }

      logger.apiError('API Error', method, url, response.status, errorMessage);
      throw new Error(errorMessage);
    }

    logger.debug('API request successful', {
      method,
      url,
      status: response.status,
    });

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    } else if (
      contentType &&
      (contentType.includes('application/octet-stream') ||
        contentType.includes('image/') ||
        contentType.includes('application/pdf'))
    ) {
      return response.blob();
    }
    return response.text();
  } // Core request method with logging and fallback
  async request(method, url, data = null, options = {}) {
    const {
      signal,
      headers: customHeaders = {},
      responseType,
      params,
    } = options;

    // Handle query parameters
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    // Get token but don't fail if it doesn't exist - let backend handle authentication
    const token = localStorage.getItem('token');
    const config = {
      method,
      signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }), // Only include auth token if available
        ...customHeaders,
      },
    };

    // Handle different data types
    if (data instanceof FormData) {
      delete config.headers['Content-Type']; // Let browser set the boundary
      config.body = data;
    } else if (data instanceof URLSearchParams) {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded';
      config.body = data;
    } else if (data) {
      config.body = JSON.stringify(data);
    }

    // Try multiple URLs for Docker compatibility
    const urls = [this.baseURL + url, this.fallbackURL + url];
    let lastError = null;

    for (let i = 0; i < urls.length; i++) {
      const fullUrl = urls[i];
      try {
        logger.debug(
          `${method} request attempt ${i + 1}/${urls.length} to ${fullUrl}`,
          {
            url: fullUrl,
            hasAuth: !!token,
            method: method,
          }
        );

        const response = await fetch(fullUrl, config);

        // Handle blob responses specially
        if (responseType === 'blob' && response.ok) {
          return response.blob();
        }

        return this.handleResponse(response, fullUrl, method);
      } catch (error) {
        console.warn(`Failed to connect to ${fullUrl}:`, error.message);
        lastError = error;

        // Continue to next URL if this one fails and we have more URLs to try
        if (i < urls.length - 1) {
          continue;
        }
      }
    }

    // If all URLs failed, log and throw the last error
    logger.apiError(lastError, url, method);
    throw (
      lastError ||
      new Error(`Failed to connect to any API endpoint for ${method} ${url}`)
    );
  }
  // Generic HTTP methods with signal support
  get(endpoint, options = {}) {
    return this.request('GET', endpoint, null, options);
  }

  post(endpoint, data, options = {}) {
    return this.request('POST', endpoint, data, options);
  }

  put(endpoint, data, options = {}) {
    return this.request('PUT', endpoint, data, options);
  }

  delete(endpoint, options = {}) {
    return this.request('DELETE', endpoint, null, options);
  }

  // Simplified API methods for backward compatibility  // Auth methods
  login(username, password, signal) {
    // FastAPI OAuth2PasswordRequestForm expects form-encoded data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    return this.request('POST', '/auth/login/', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      signal,
    });
  }

  register(username, password, email, fullName, signal) {
    return this.post(
      '/auth/register/',
      {
        username,
        password,
        email,
        full_name: fullName,
      },
      { signal }
    );
  }

  // Update user profile
  updateUserProfile(profileData, signal) {
    return this.put('/auth/profile/', profileData, { signal });
  }

  changePassword(passwordData, signal) {
    return this.post('/auth/change-password', passwordData, { signal });
  }

  // Patient methods
  getCurrentPatient(signal) {
    return this.get('/patients/me', { signal });
  }

  createCurrentPatient(patientData, signal) {
    return this.post('/patients/me', patientData, { signal });
  }

  updateCurrentPatient(patientData, signal) {
    return this.put('/patients/me', patientData, { signal });
  }

  async getRecentActivity(patientId = null, signal) {
    // Always send patient_id parameter if we have one, even if it's 0
    const params =
      patientId !== null && patientId !== undefined
        ? { patient_id: patientId }
        : {};

    try {
      const result = await this.get('/patients/recent-activity/', {
        params,
        signal,
      });
      return result;
    } catch (error) {
      throw error;
    }
  }

  getDashboardStats(patientId, signal) {
    // Support both Phase 1 patient switching and legacy single patient mode
    if (patientId) {
      return this.get('/patients/me/dashboard-stats', {
        params: { patient_id: patientId },
        signal,
      });
    } else {
      // Fallback for legacy mode
      return this.get('/patients/me/dashboard-stats', { signal });
    }
  }

  // Generic entity methods using the entity relationship system
  getEntities(entityType, signal) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    return this.get(`/${apiPath}/`, { signal });
  }

  getEntity(entityType, entityId, signal) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    return this.get(`/${apiPath}/${entityId}`, { signal });
  }

  createEntity(entityType, entityData, signal) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    return this.post(`/${apiPath}/`, entityData, { signal });
  }

  updateEntity(entityType, entityId, entityData, signal, patientId = null) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    let url = `/${apiPath}/${entityId}`;
    
    // Add patient_id query parameter if provided
    if (patientId !== null) {
      url += `?patient_id=${patientId}`;
    }
    
    logger.debug('api_update_entity', 'Update entity URL construction', {
      entityType,
      entityId,
      apiPath,
      url,
      patientId,
      baseURL: this.baseURL,
      fallbackURL: this.fallbackURL,
    });
    return this.put(url, entityData, { signal });
  }

  deleteEntity(entityType, entityId, signal, patientId = null) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    let url = `/${apiPath}/${entityId}`;
    
    // Add patient_id query parameter if provided
    if (patientId !== null) {
      url += `?patient_id=${patientId}`;
    }
    
    return this.delete(url, { signal });
  }

  getEntitiesWithFilters(entityType, filters = {}, signal) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, value);
      }
    });
    const queryString = params.toString();
    return this.get(`/${apiPath}/${queryString ? `?${queryString}` : ''}`, {
      signal,
    });
  }

  getPatientEntities(entityType, patientId, signal) {
    const apiPath = ENTITY_TO_API_PATH[entityType] || entityType;
    const url = `/${apiPath}/?patient_id=${patientId}`;
    logger.debug('api_patient_entities', 'Fetching patient entities', {
      entityType,
      patientId,
      url,
      apiPath,
    });
    return this.get(url, { signal });
  }

  // Lab Result methods
  getLabResults(signal) {
    return this.getEntities(ENTITY_TYPES.LAB_RESULT, signal);
  }
  getPatientLabResults(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.LAB_RESULT, patientId, signal);
  }
  getLabResult(labResultId, signal) {
    return this.getEntity(ENTITY_TYPES.LAB_RESULT, labResultId, signal);
  }

  createLabResult(labResultData, signal) {
    return this.createEntity(ENTITY_TYPES.LAB_RESULT, labResultData, signal);
  }

  updateLabResult(labResultId, labResultData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.LAB_RESULT,
      labResultId,
      labResultData,
      signal
    );
  }

  deleteLabResult(labResultId, signal) {
    return this.deleteEntity(ENTITY_TYPES.LAB_RESULT, labResultId, signal);
  }

  // ==========================================
  // GENERIC FILE MANAGEMENT METHODS
  // ==========================================

  /**
   * Generic file management methods that work with any entity type
   * Supports: lab-result, insurance, visit, procedure, etc.
   */

  // Map entity types to their file endpoint paths
  getFileEndpoint(entityType, entityId) {
    // Use the new generic backend API endpoints
    return `/entity-files/${entityType}/${entityId}/files`;
  }

  // Get all files for an entity
  getEntityFiles(entityType, entityId, signal) {
    try {
      const endpoint = this.getFileEndpoint(entityType, entityId);

      logger.debug('api_get_entity_files', 'Fetching entity files', {
        entityType,
        entityId,
        endpoint,
        component: 'ApiService',
      });

      return this.get(endpoint, { 
        signal,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
    } catch (error) {
      logger.error('api_get_entity_files_error', 'Failed to get entity files', {
        entityType,
        entityId,
        error: error.message,
        component: 'ApiService',
      });
      throw error;
    }
  }

  // Upload file to an entity
  uploadEntityFile(
    entityType,
    entityId,
    file,
    description = '',
    category = '',
    storageBackend = undefined,
    signal
  ) {
    const endpoint = this.getFileEndpoint(entityType, entityId);

    const formData = new FormData();
    formData.append('file', file);
    if (description && description.trim()) {
      formData.append('description', description.trim());
    }
    if (category && category.trim()) {
      formData.append('category', category.trim());
    }
    // Only send storage_backend if explicitly specified, otherwise let backend use user's default
    if (storageBackend) {
      formData.append('storage_backend', storageBackend);
    }

    logger.info('api_upload_entity_file', 'Uploading file to entity', {
      entityType,
      entityId,
      fileName: file.name,
      fileSize: file.size,
      hasDescription: !!description,
      hasCategory: !!category,
      storageBackend,
      actualStorageBackend: storageBackend || 'local',
      endpoint,
      component: 'ApiService',
    });

    return this.post(endpoint, formData, { signal })
      .then(response => {
        logger.info('api_upload_entity_file_response', 'File upload response received', {
          response: JSON.stringify(response),
          hasPaperlessTaskUuid: !!response?.paperless_task_uuid,
          component: 'ApiService',
        });
        
        return response;
      })
      .catch(error => {
        logger.error(
          'api_upload_entity_file_error',
          'Failed to upload entity file',
          {
            entityType,
            entityId,
            fileName: file?.name,
            error: error.message,
            component: 'ApiService',
          }
        );
        throw error;
      });
  }

  // Upload file to an entity with Paperless task status monitoring
  async uploadEntityFileWithTaskMonitoring(
    entityType,
    entityId,
    file,
    description = '',
    category = '',
    storageBackend = undefined,
    signal,
    onProgress = null
  ) {
    try {
      logger.info('api_upload_entity_file_with_monitoring', 'Starting monitored upload', {
        entityType,
        entityId,
        fileName: file.name,
        fileSize: file.size,
        storageBackend,
        component: 'ApiService',
      });

      // Perform the initial upload
      const uploadResult = await this.uploadEntityFile(
        entityType,
        entityId,
        file,
        description,
        category,
        storageBackend,
        signal
      );

      logger.info('api_upload_result', 'Upload result received', {
        uploadResult: JSON.stringify(uploadResult),
        hasTaskUuid: !!uploadResult?.paperless_task_uuid,
        storageBackend,
        component: 'ApiService',
      });

      // If not using Paperless or no task UUID returned, return immediately
      if (storageBackend !== 'paperless' || !uploadResult?.paperless_task_uuid) {
        logger.info('api_upload_no_monitoring_needed', 'Upload completed without task monitoring', {
          entityType,
          entityId,
          fileName: file.name,
          storageBackend,
          hasTaskUuid: !!uploadResult?.paperless_task_uuid,
          component: 'ApiService',
        });
        return {
          ...uploadResult,
          taskMonitored: false,
          documentId: null,
          isDuplicate: false
        };
      }

      // Monitor Paperless task status
      const taskUuid = uploadResult.paperless_task_uuid;
      
      if (onProgress) {
        onProgress({ status: 'processing', message: 'Processing document in Paperless...' });
      }

      logger.info('api_upload_task_monitoring', 'Starting Paperless task monitoring', {
        entityType,
        entityId,
        fileName: file.name,
        taskUuid,
        component: 'ApiService',
      });

      // Import the pollPaperlessTaskStatus function
      const { pollPaperlessTaskStatus } = await import('./paperlessApi');
      
      // Poll task status
      const taskResult = await pollPaperlessTaskStatus(taskUuid, 30, 1000);

      logger.info('api_upload_task_complete', 'Paperless task monitoring completed', {
        entityType,
        entityId,
        fileName: file.name,
        taskUuid,
        taskStatus: taskResult.status,
        hasError: !!taskResult.error,
        hasDocumentId: !!(taskResult.result?.document_id || taskResult.document_id),
        component: 'ApiService',
      });

      // Process task result directly
      logger.debug('api_upload_task_processing', 'Processing task result', {
        taskResultStatus: taskResult?.status,
        taskResultErrorType: taskResult?.error_type,
        taskResultHasResult: !!taskResult?.result,
        component: 'ApiService',
      });

      // Check if task was successful
      const isSuccess = taskResult?.status === 'SUCCESS' && 
                       (taskResult?.id || taskResult?.related_document || taskResult?.result?.document_id || taskResult?.document_id);
      
      // Check if task failed due to duplicate
      const isDuplicate = taskResult?.error_type === 'duplicate' || 
                         (taskResult?.status === 'FAILURE' && 
                          taskResult?.result && 
                          (taskResult.result.toLowerCase().includes('duplicate') || 
                           taskResult.result.toLowerCase().includes('already exists')));
      
      // Get user-friendly error message based on error type
      const getUserFriendlyErrorMessage = (taskResult, fileName) => {
        const errorType = taskResult?.error_type;
        const originalError = taskResult?.result || 'Upload failed';
        
        switch (errorType) {
          case 'duplicate':
            return `"${fileName}" already exists in Paperless. This document appears to be a duplicate.`;
          case 'corrupted_file':
            return `"${fileName}" appears to be corrupted or in an unsupported format. Please check the file and try again.`;
          case 'permission_error':
            return `Permission denied uploading "${fileName}". Please check your Paperless access rights.`;
          case 'file_too_large':
            return `"${fileName}" is too large for Paperless. Please reduce the file size or check your Paperless configuration.`;
          case 'storage_full':
            return `Paperless storage is full. Unable to upload "${fileName}". Please contact your administrator.`;
          case 'ocr_failed':
            return `"${fileName}" was uploaded but Paperless had trouble extracting text from it. The document is still stored.`;
          case 'network_error':
            return `Network error uploading "${fileName}" to Paperless. Please check your connection and try again.`;
          case 'processing_error':
          default:
            return `Paperless was unable to process "${fileName}". Please try again or contact support if the problem persists.`;
        }
      };
      
      // Extract and validate document ID if successful
      let documentId = null;
      if (isSuccess) {
        // Check multiple possible locations for document ID
        const rawDocumentId = taskResult?.id || 
                             taskResult?.related_document || 
                             taskResult?.result?.document_id || 
                             taskResult?.document_id;
        
        // Validate document ID - reject invalid values like "unknown"
        if (rawDocumentId && 
            String(rawDocumentId).toLowerCase() !== 'unknown' && 
            String(rawDocumentId).toLowerCase() !== 'none' && 
            String(rawDocumentId).toLowerCase() !== 'null' && 
            String(rawDocumentId) !== '' &&
            !isNaN(rawDocumentId) && 
            parseInt(rawDocumentId) > 0) {
          documentId = rawDocumentId;
        } else {
          // Invalid document ID - trigger fallback search
          logger.warn('api_upload_invalid_document_id', 'Task returned invalid document ID, attempting fallback search', {
            rawDocumentId,
            fileName: file.name,
            taskUuid,
            component: 'ApiService',
          });
          
          try {
            // Import and call fallback search
            const { searchDocumentByFilenameAndTime } = await import('./paperlessApi');
            const fallbackDocumentId = await searchDocumentByFilenameAndTime(file.name);
            
            if (fallbackDocumentId) {
              documentId = fallbackDocumentId;
              logger.info('api_upload_fallback_success', 'Fallback search found document ID', {
                fileName: file.name,
                fallbackDocumentId,
                originalTaskResult: rawDocumentId,
                component: 'ApiService',
              });
            } else {
              logger.error('api_upload_fallback_failed', 'Fallback search could not find document', {
                fileName: file.name,
                originalTaskResult: rawDocumentId,
                component: 'ApiService',
              });
              // Keep documentId as null to indicate failure
            }
          } catch (fallbackError) {
            logger.error('api_upload_fallback_error', 'Error during fallback search', {
              fileName: file.name,
              originalTaskResult: rawDocumentId,
              error: fallbackError.message,
              component: 'ApiService',
            });
            // Keep documentId as null to indicate failure
          }
        }
      }

      logger.debug('api_upload_task_processed', 'Task result processed', {
        isSuccess,
        isDuplicate,
        documentId,
        component: 'ApiService',
      });

      if (onProgress) {
        const status = isSuccess ? 'completed' : 
                      isDuplicate ? 'completed_duplicate' : 
                      'failed';
        
        let message;
        if (isSuccess) {
          message = 'Document processed successfully';
        } else if (isDuplicate) {
          message = getUserFriendlyErrorMessage(taskResult, file.name);
        } else {
          message = getUserFriendlyErrorMessage(taskResult, file.name);
        }
        
        onProgress({ 
          status, 
          message, 
          isDuplicate,
          errorType: taskResult?.error_type 
        });
      }

      return {
        ...uploadResult,
        taskMonitored: true,
        taskResult,
        documentId,
        isDuplicate,
        success: isSuccess
      };

    } catch (error) {
      logger.error('api_upload_entity_file_monitoring_error', 'Failed to upload and monitor entity file', {
        entityType,
        entityId,
        fileName: file?.name,
        error: error.message,
        component: 'ApiService',
      });
      
      // Re-throw with additional context
      const enhancedError = new Error(`Upload monitoring failed: ${error.message}`);
      enhancedError.originalError = error;
      throw enhancedError;
    }
  }


  // View file in new tab (generic - file ID is enough)
  async viewEntityFile(fileId, fileName, signal) {
    try {
      logger.info('api_view_entity_file', 'Opening entity file for viewing', {
        fileId,
        fileName,
        component: 'ApiService',
      });

      // Get authentication token
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required to view files');
      }

      // Validate and check token (with improved error handling)
      try {
        // Validate token format
        if (typeof token !== 'string' || token.trim() === '') {
          throw new Error('Token is empty or not a string');
        }

        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
          throw new Error(`Invalid JWT format - expected 3 parts, got ${tokenParts.length}`);
        }

        // More robust JWT payload parsing
        let payload;
        try {
          // Add padding if needed for base64 decoding
          let base64Payload = tokenParts[1];
          while (base64Payload.length % 4) {
            base64Payload += '=';
          }
          const decodedPayload = atob(base64Payload);
          payload = JSON.parse(decodedPayload);
        } catch (parseError) {
          logger.warn('jwt_payload_parse_warning', 'JWT payload parsing failed but continuing with file view', {
            error: parseError.message,
            fileId,
            fileName,
            component: 'ApiService',
          });
          // For file viewing, we'll continue even if payload parsing fails
          // as long as we have a token - the server will validate it properly
          payload = {};
        }
        
        // Only validate claims if we successfully parsed the payload
        if (payload.exp) {
          const currentTime = Date.now() / 1000;
          if (payload.exp < currentTime) {
            throw new Error('Session expired. Please log in again.');
          }
        }
      } catch (e) {
        // Only throw errors for critical authentication issues
        if (e.message.includes('Session expired') || 
            e.message.includes('Token is empty') ||
            e.message.includes('Invalid JWT format')) {
          throw e;
        }
        // For other token validation issues during file viewing, log warning but continue
        logger.warn('jwt_validation_warning', 'Token validation warning during file view, continuing anyway', {
          error: e.message,
          fileId,
          fileName,
          component: 'ApiService',
        });
      }

      // Construct view URL with authentication token
      // Use the base URL from environment variable, removing /api/v1 suffix if present
      const envBaseUrl = process.env.REACT_APP_API_URL || '/api/v1';
      const baseUrl = envBaseUrl.endsWith('/api/v1') ? envBaseUrl.slice(0, -7) : envBaseUrl;
      const viewUrl = `${baseUrl}/api/v1/entity-files/files/${fileId}/view?token=${encodeURIComponent(token)}`;

      // Open in new tab
      const newWindow = window.open(viewUrl, '_blank', 'noopener,noreferrer');
      
      // Note: In modern browsers, window.open() may return null even when successful
      // due to security restrictions, especially with 'noopener' flag
      // We'll log a warning but not fail the operation since the file often opens anyway
      if (!newWindow) {
        logger.warn('popup_detection_warning', 'window.open returned null, but file may still open', {
          fileId,
          fileName,
          viewUrl: viewUrl.replace(/token=[^&]+/, 'token=***'),
          component: 'ApiService',
        });
        // Don't throw error - let the operation succeed since file often opens despite null return
      }

      // Note: window.open() for external URLs doesn't provide success/failure feedback
      // We log success here assuming the tab opened successfully
      logger.info('api_view_entity_file_success', 'File viewer opened successfully', {
        fileId,
        fileName,
        viewUrl: viewUrl.replace(/token=[^&]+/, 'token=***'), // Hide token in logs
        component: 'ApiService',
      });
      
      // Return success - we can't actually verify if the file loaded successfully
      // since it opens in a new tab/window, but if window.open() didn't return null,
      // the tab was created
      return { success: true, message: 'File opened in new tab' };
    } catch (error) {
      logger.error('api_view_entity_file_error', 'Failed to view entity file', {
        fileId,
        fileName,
        error: error.message,
        errorStack: error.stack,
        errorType: error.constructor.name,
        component: 'ApiService',
      });
      throw error;
    }
  }

  // Download file (generic - file ID is enough)
  async downloadEntityFile(fileId, fileName, signal) {
    try {
      logger.info('api_download_entity_file', 'Downloading entity file', {
        fileId,
        fileName,
        component: 'ApiService',
      });

      const blob = await this.get(`/entity-files/files/${fileId}/download`, {
        responseType: 'blob',
        signal,
      });

      // Handle blob download in browser
      if (blob instanceof Blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = fileName || `file_${fileId}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        logger.info(
          'api_download_entity_file_success',
          'File download completed',
          {
            fileId,
            fileName,
            component: 'ApiService',
          }
        );
      } else {
        throw new Error('Invalid blob response from server');
      }
    } catch (error) {
      logger.error(
        'api_download_entity_file_error',
        'Failed to download entity file',
        {
          fileId,
          fileName,
          error: error.message,
          component: 'ApiService',
        }
      );
      throw error;
    }
  }

  // Delete file (generic - file ID is enough)
  deleteEntityFile(fileId, signal) {
    try {
      logger.info('api_delete_entity_file', 'Deleting entity file', {
        fileId,
        component: 'ApiService',
      });

      return this.delete(`/entity-files/files/${fileId}`, { signal });
    } catch (error) {
      logger.error(
        'api_delete_entity_file_error',
        'Failed to delete entity file',
        {
          fileId,
          error: error.message,
          component: 'ApiService',
        }
      );
      throw error;
    }
  }

  // Batch get file counts for multiple entities (performance optimization)
  getMultipleEntityFilesCounts(entityType, entityIds, signal) {
    try {
      logger.debug('api_batch_file_counts', 'Getting batch file counts', {
        entityType,
        entityCount: entityIds?.length,
        component: 'ApiService',
      });

      return this.post(
        '/entity-files/files/batch-counts',
        {
          entity_type: entityType,
          entity_ids: entityIds,
        },
        { signal }
      );
    } catch (error) {
      logger.error(
        'api_batch_file_counts_error',
        'Failed to get batch file counts',
        {
          entityType,
          entityCount: entityIds?.length,
          error: error.message,
          component: 'ApiService',
        }
      );
      throw error;
    }
  }

  // Check Paperless document sync status
  async checkPaperlessSyncStatus(signal) {
    // Create a timeout signal to prevent hanging requests
    let timeoutId;
    const timeoutSignal = new AbortController();
    
    try {
      logger.debug('api_paperless_sync_check', 'Checking Paperless sync status', {
        component: 'ApiService',
      });

      if (!signal) {
        // Set 30-second timeout for sync check requests
        timeoutId = setTimeout(() => {
          timeoutSignal.abort();
        }, 30000);
      }

      const finalSignal = signal || timeoutSignal.signal;

      const result = await this.post('/entity-files/sync/paperless', {}, { 
        signal: finalSignal,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });

      // Clear timeout if request completed successfully
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      logger.info('api_paperless_sync_check_success', 'Paperless sync status check completed', {
        filesChecked: Object.keys(result || {}).length,
        component: 'ApiService',
      });

      return result;
    } catch (error) {
      // Clear timeout if request failed
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Enhanced error logging for better debugging
      logger.error(
        'api_paperless_sync_check_error',
        'Failed to check Paperless sync status',
        {
          error: error.message,
          errorStack: error.stack,
          errorResponse: error.response,
          isAbortError: error.name === 'AbortError',
          component: 'ApiService',
        }
      );

      // Provide more specific error messages for common issues
      let enhancedError = error;
      if (error.name === 'AbortError') {
        enhancedError = new Error('Sync check timed out. Please check your Paperless connection and try again.');
      } else if (error.message?.includes('401') || error.message?.includes('Unauthorized')) {
        enhancedError = new Error('Authentication failed. Please check your Paperless credentials in Settings.');
      } else if (error.message?.includes('403') || error.message?.includes('Forbidden')) {
        enhancedError = new Error('Access denied. Please verify your Paperless permissions.');
      } else if (error.message?.includes('404')) {
        enhancedError = new Error('Paperless API endpoint not found. Please check your Paperless URL configuration.');
      } else if (error.message?.includes('500')) {
        enhancedError = new Error('Paperless server error. Please check your Paperless instance status.');
      } else if (error.message?.includes('ECONNREFUSED') || error.message?.includes('Network')) {
        enhancedError = new Error('Cannot connect to Paperless. Please check your Paperless URL and network connection.');
      }

      enhancedError.originalError = error;
      throw enhancedError;
    }
  }

  // Update processing files status by checking Paperless task completion
  updateProcessingFiles(signal) {
    try {
      logger.info('api_update_processing_files', 'Updating processing files status', {
        component: 'ApiService',
      });

      return this.post('/entity-files/processing/update', {}, { 
        signal,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
    } catch (error) {
      logger.error(
        'api_update_processing_files_error',
        'Failed to update processing files status',
        {
          error: error.message,
          component: 'ApiService',
        }
      );
      throw error;
    }
  }

  // ==========================================
  // BACKWARD COMPATIBILITY WRAPPERS
  // ==========================================

  /**
   * Maintain backward compatibility with existing LabResult file methods
   * These now use the generic methods internally
   */

  // Backward compatibility for lab result files
  getLabResultFiles(labResultId, signal) {
    return this.getEntityFiles('lab-result', labResultId, signal);
  }

  uploadLabResultFile(
    labResultId,
    file,
    description = '',
    category = '',
    storageBackend = undefined,
    signal
  ) {
    return this.uploadEntityFile(
      'lab-result',
      labResultId,
      file,
      description,
      category,
      storageBackend,
      signal
    );
  }

  downloadLabResultFile(fileId, fileName, signal) {
    return this.downloadEntityFile(fileId, fileName, signal);
  }

  deleteLabResultFile(fileId, signal) {
    return this.deleteEntityFile(fileId, signal);
  }

  // Lab Result - Condition Relationship methods
  getLabResultConditions(labResultId, signal) {
    return this.get(`/lab-results/${labResultId}/conditions`, { signal });
  }
  createLabResultCondition(labResultId, conditionData, signal, patientId = null) {
    let url = `/lab-results/${labResultId}/conditions`;
    if (patientId !== null) {
      url += `?patient_id=${patientId}`;
    }
    return this.post(url, conditionData, {
      signal,
    });
  }
  updateLabResultCondition(labResultId, relationshipId, conditionData, signal) {
    return this.put(
      `/lab-results/${labResultId}/conditions/${relationshipId}`,
      conditionData,
      { signal }
    );
  }
  deleteLabResultCondition(labResultId, relationshipId, signal) {
    return this.delete(
      `/lab-results/${labResultId}/conditions/${relationshipId}`,
      { signal }
    );
  }

  // Medication methods
  getMedications(signal) {
    return this.getEntities(ENTITY_TYPES.MEDICATION, signal);
  }
  getPatientMedications(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.MEDICATION, patientId, signal);
  }
  getMedicationsWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(
      ENTITY_TYPES.MEDICATION,
      filters,
      signal
    );
  }

  createMedication(medicationData, signal) {
    // Clean up empty strings which might cause backend validation issues
    const cleanPayload = {};
    Object.keys(medicationData).forEach(key => {
      const value = medicationData[key];
      if (value !== '' && value !== null && value !== undefined) {
        cleanPayload[key] = value;
      }
    });

    // Ensure required fields
    if (!cleanPayload.medication_name) {
      throw new Error('Medication name is required');
    }

    return this.post(`/medications/`, cleanPayload, { signal });
  }
  updateMedication(medicationId, medicationData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.MEDICATION,
      medicationId,
      medicationData,
      signal
    );
  }

  deleteMedication(medicationId, signal) {
    return this.deleteEntity(ENTITY_TYPES.MEDICATION, medicationId, signal);
  }

  // Insurance methods
  getInsurances(signal) {
    return this.getEntities(ENTITY_TYPES.INSURANCE, signal);
  }
  getPatientInsurances(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.INSURANCE, patientId, signal);
  }
  getInsurancesWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(ENTITY_TYPES.INSURANCE, filters, signal);
  }

  createInsurance(insuranceData, signal) {
    // Clean up empty strings which might cause backend validation issues
    const cleanPayload = {};
    Object.keys(insuranceData).forEach(key => {
      const value = insuranceData[key];
      if (value !== '' && value !== null && value !== undefined) {
        cleanPayload[key] = value;
      }
    });

    // Ensure required fields
    if (!cleanPayload.insurance_type) {
      throw new Error('Insurance type is required');
    }
    if (!cleanPayload.company_name) {
      throw new Error('Insurance company name is required');
    }
    if (!cleanPayload.member_name) {
      throw new Error('Member name is required');
    }
    if (!cleanPayload.member_id) {
      throw new Error('Member ID is required');
    }

    return this.createEntity(ENTITY_TYPES.INSURANCE, cleanPayload, signal);
  }
  updateInsurance(insuranceId, insuranceData, signal) {
    logger.debug('api_update_insurance', 'Updating insurance via API', {
      insuranceId,
      insuranceData,
      hasData: !!insuranceData,
    });
    return this.updateEntity(
      ENTITY_TYPES.INSURANCE,
      insuranceId,
      insuranceData,
      signal
    );
  }

  deleteInsurance(insuranceId, signal) {
    return this.deleteEntity(ENTITY_TYPES.INSURANCE, insuranceId, signal);
  }

  setPrimaryInsurance(insuranceId, signal) {
    return this.request(
      'PATCH',
      `/insurances/${insuranceId}/set-primary`,
      null,
      { signal }
    );
  }

  // Immunization methods
  getImmunizations(signal) {
    return this.getEntities(ENTITY_TYPES.IMMUNIZATION, signal);
  }
  getPatientImmunizations(patientId, signal) {
    return this.getPatientEntities(
      ENTITY_TYPES.IMMUNIZATION,
      patientId,
      signal
    );
  }
  getImmunizationsWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(
      ENTITY_TYPES.IMMUNIZATION,
      filters,
      signal
    );
  }

  createImmunization(immunizationData, signal) {
    return this.createEntity(
      ENTITY_TYPES.IMMUNIZATION,
      immunizationData,
      signal
    );
  }
  updateImmunization(immunizationId, immunizationData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.IMMUNIZATION,
      immunizationId,
      immunizationData,
      signal
    );
  }

  deleteImmunization(immunizationId, signal) {
    return this.deleteEntity(ENTITY_TYPES.IMMUNIZATION, immunizationId, signal);
  }

  // Practitioner methods
  getPractitioners(signal) {
    return this.getEntities(ENTITY_TYPES.PRACTITIONER, signal);
  }

  getPractitioner(practitionerId, signal) {
    return this.getEntity(ENTITY_TYPES.PRACTITIONER, practitionerId, signal);
  }
  getPractitionersWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(
      ENTITY_TYPES.PRACTITIONER,
      filters,
      signal
    );
  }

  createPractitioner(practitionerData, signal) {
    return this.createEntity(
      ENTITY_TYPES.PRACTITIONER,
      practitionerData,
      signal
    );
  }

  updatePractitioner(practitionerId, practitionerData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.PRACTITIONER,
      practitionerId,
      practitionerData,
      signal
    );
  }

  deletePractitioner(practitionerId, signal) {
    return this.deleteEntity(ENTITY_TYPES.PRACTITIONER, practitionerId, signal);
  }

  // Pharmacy methods
  getPharmacies(signal) {
    return this.getEntities(ENTITY_TYPES.PHARMACY, signal);
  }

  getPharmacy(pharmacyId, signal) {
    return this.getEntity(ENTITY_TYPES.PHARMACY, pharmacyId, signal);
  }

  createPharmacy(pharmacyData, signal) {
    return this.createEntity(ENTITY_TYPES.PHARMACY, pharmacyData, signal);
  }

  updatePharmacy(pharmacyId, pharmacyData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.PHARMACY,
      pharmacyId,
      pharmacyData,
      signal
    );
  }

  deletePharmacy(pharmacyId, signal) {
    return this.deleteEntity(ENTITY_TYPES.PHARMACY, pharmacyId, signal);
  }

  // Allergy methods
  getAllergies(signal) {
    return this.getEntities(ENTITY_TYPES.ALLERGY, signal);
  }
  getPatientAllergies(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.ALLERGY, patientId, signal);
  }
  getAllergy(allergyId, signal) {
    return this.getEntity(ENTITY_TYPES.ALLERGY, allergyId, signal);
  }

  createAllergy(allergyData, signal) {
    return this.createEntity(ENTITY_TYPES.ALLERGY, allergyData, signal);
  }

  updateAllergy(allergyId, allergyData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.ALLERGY,
      allergyId,
      allergyData,
      signal
    );
  }

  deleteAllergy(allergyId, signal) {
    return this.deleteEntity(ENTITY_TYPES.ALLERGY, allergyId, signal);
  }

  // Treatment methods
  getTreatments(signal) {
    return this.getEntities(ENTITY_TYPES.TREATMENT, signal);
  }
  getPatientTreatments(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.TREATMENT, patientId, signal);
  }
  getTreatment(treatmentId, signal) {
    return this.getEntity(ENTITY_TYPES.TREATMENT, treatmentId, signal);
  }
  getTreatmentsWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(ENTITY_TYPES.TREATMENT, filters, signal);
  }

  createTreatment(treatmentData, signal) {
    return this.createEntity(ENTITY_TYPES.TREATMENT, treatmentData, signal);
  }

  updateTreatment(treatmentId, treatmentData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.TREATMENT,
      treatmentId,
      treatmentData,
      signal
    );
  }

  deleteTreatment(treatmentId, signal) {
    return this.deleteEntity(ENTITY_TYPES.TREATMENT, treatmentId, signal);
  }

  // Procedure methods
  getProcedures(signal) {
    return this.getEntities(ENTITY_TYPES.PROCEDURE, signal);
  }
  getPatientProcedures(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.PROCEDURE, patientId, signal);
  }
  getProcedure(procedureId, signal) {
    return this.getEntity(ENTITY_TYPES.PROCEDURE, procedureId, signal);
  }
  getProceduresWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(ENTITY_TYPES.PROCEDURE, filters, signal);
  }

  createProcedure(procedureData, signal) {
    return this.createEntity(ENTITY_TYPES.PROCEDURE, procedureData, signal);
  }
  updateProcedure(procedureId, procedureData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.PROCEDURE,
      procedureId,
      procedureData,
      signal
    );
  }

  deleteProcedure(procedureId, signal) {
    return this.deleteEntity(ENTITY_TYPES.PROCEDURE, procedureId, signal);
  }

  // Condition methods
  getConditions(signal) {
    return this.getEntities(ENTITY_TYPES.CONDITION, signal);
  }
  getPatientConditions(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.CONDITION, patientId, signal);
  }
  getCondition(conditionId, signal) {
    return this.getEntity(ENTITY_TYPES.CONDITION, conditionId, signal);
  }
  getConditionsWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(ENTITY_TYPES.CONDITION, filters, signal);
  }

  createCondition(conditionData, signal) {
    return this.createEntity(ENTITY_TYPES.CONDITION, conditionData, signal);
  }

  updateCondition(conditionId, conditionData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.CONDITION,
      conditionId,
      conditionData,
      signal
    );
  }

  deleteCondition(conditionId, signal) {
    return this.deleteEntity(ENTITY_TYPES.CONDITION, conditionId, signal);
  }

  getConditionsDropdown(activeOnly = true, signal) {
    const url = `/conditions/dropdown?active_only=${activeOnly}`;
    return this.get(url, { signal });
  }

  // Condition - Medication Relationship methods
  getConditionMedications(conditionId, signal) {
    return this.get(`/conditions/condition-medications/${conditionId}`, { signal });
  }
  createConditionMedication(conditionId, medicationData, signal) {
    return this.post(`/conditions/${conditionId}/medications`, medicationData, {
      signal,
    });
  }
  updateConditionMedication(
    conditionId,
    relationshipId,
    medicationData,
    signal
  ) {
    return this.put(
      `/conditions/${conditionId}/medications/${relationshipId}`,
      medicationData,
      { signal }
    );
  }
  deleteConditionMedication(conditionId, relationshipId, signal) {
    return this.delete(
      `/conditions/${conditionId}/medications/${relationshipId}`,
      { signal }
    );
  }

  // Medication - Condition Relationship methods (for showing conditions on medication view)
  getMedicationConditions(medicationId, signal) {
    return this.get(`/conditions/medication/${medicationId}/conditions`, {
      signal,
    });
  }

  // Encounter methods
  getEncounters(signal) {
    return this.getEntities(ENTITY_TYPES.ENCOUNTER, signal);
  }
  getPatientEncounters(patientId, signal) {
    return this.getPatientEntities(ENTITY_TYPES.ENCOUNTER, patientId, signal);
  }
  getEncounter(encounterId, signal) {
    return this.getEntity(ENTITY_TYPES.ENCOUNTER, encounterId, signal);
  }
  getEncountersWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(ENTITY_TYPES.ENCOUNTER, filters, signal);
  }

  createEncounter(encounterData, signal) {
    return this.createEntity(ENTITY_TYPES.ENCOUNTER, encounterData, signal);
  }

  updateEncounter(encounterId, encounterData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.ENCOUNTER,
      encounterId,
      encounterData,
      signal
    );
  }

  deleteEncounter(encounterId, signal) {
    return this.deleteEntity(ENTITY_TYPES.ENCOUNTER, encounterId, signal);
  }

  // Emergency Contact methods
  getEmergencyContacts(signal) {
    return this.getEntities(ENTITY_TYPES.EMERGENCY_CONTACT, signal);
  }
  getPatientEmergencyContacts(patientId, signal) {
    return this.getPatientEntities(
      ENTITY_TYPES.EMERGENCY_CONTACT,
      patientId,
      signal
    );
  }
  getEmergencyContact(emergencyContactId, signal) {
    return this.getEntity(
      ENTITY_TYPES.EMERGENCY_CONTACT,
      emergencyContactId,
      signal
    );
  }

  createEmergencyContact(emergencyContactData, signal) {
    return this.createEntity(
      ENTITY_TYPES.EMERGENCY_CONTACT,
      emergencyContactData,
      signal
    );
  }

  updateEmergencyContact(emergencyContactId, emergencyContactData, signal) {
    return this.updateEntity(
      ENTITY_TYPES.EMERGENCY_CONTACT,
      emergencyContactId,
      emergencyContactData,
      signal
    );
  }

  deleteEmergencyContact(emergencyContactId, signal) {
    return this.deleteEntity(
      ENTITY_TYPES.EMERGENCY_CONTACT,
      emergencyContactId,
      signal
    );
  }

  // Generic method for fetching entities with relationship filters
  getRelatedEntities(entityType, filters = {}, signal) {
    return this.getEntitiesWithFilters(entityType, filters, signal);
  }

  // Family Member methods
  getFamilyMembers(signal) {
    return this.getEntities(ENTITY_TYPES.FAMILY_MEMBER, signal);
  }
  getPatientFamilyMembers(patientId, signal) {
    return this.getPatientEntities(
      ENTITY_TYPES.FAMILY_MEMBER,
      patientId,
      signal
    );
  }
  getFamilyMember(familyMemberId, signal) {
    return this.getEntity(ENTITY_TYPES.FAMILY_MEMBER, familyMemberId, signal);
  }
  getFamilyMembersWithFilters(filters = {}, signal) {
    return this.getEntitiesWithFilters(
      ENTITY_TYPES.FAMILY_MEMBER,
      filters,
      signal
    );
  }

  createFamilyMember(familyMemberData, signal) {
    return this.createEntity(
      ENTITY_TYPES.FAMILY_MEMBER,
      familyMemberData,
      signal
    );
  }
  updateFamilyMember(familyMemberId, familyMemberData, signal, patientId = null) {
    return this.updateEntity(
      ENTITY_TYPES.FAMILY_MEMBER,
      familyMemberId,
      familyMemberData,
      signal,
      patientId
    );
  }
  deleteFamilyMember(familyMemberId, signal, patientId = null) {
    return this.deleteEntity(
      ENTITY_TYPES.FAMILY_MEMBER,
      familyMemberId,
      signal,
      patientId
    );
  }

  // Family Condition methods (nested under family members)
  getFamilyMemberConditions(familyMemberId, signal) {
    return this.get(`/family-members/${familyMemberId}/conditions`, { signal });
  }
  createFamilyCondition(familyMemberId, conditionData, signal, patientId = null) {
    let url = `/family-members/${familyMemberId}/conditions`;
    if (patientId !== null) {
      url += `?patient_id=${patientId}`;
    }
    return this.post(url, conditionData, { signal });
  }
  updateFamilyCondition(familyMemberId, conditionId, conditionData, signal, patientId = null) {
    let url = `/family-members/${familyMemberId}/conditions/${conditionId}`;
    if (patientId !== null) {
      url += `?patient_id=${patientId}`;
    }
    return this.put(url, conditionData, { signal });
  }
  deleteFamilyCondition(familyMemberId, conditionId, signal, patientId = null) {
    let url = `/family-members/${familyMemberId}/conditions/${conditionId}`;
    if (patientId !== null) {
      url += `?patient_id=${patientId}`;
    }
    return this.delete(url, { signal });
  }

  // Search family members
  searchFamilyMembers(searchTerm, signal) {
    return this.get(
      `/family-members/search/?name=${encodeURIComponent(searchTerm)}`,
      { signal }
    );
  }
}

export const apiService = new ApiService();
export default apiService;

// V1 Patient Management Services
export { default as patientApi } from './patientApi';
export { default as patientSharingApi } from './patientSharingApi';
