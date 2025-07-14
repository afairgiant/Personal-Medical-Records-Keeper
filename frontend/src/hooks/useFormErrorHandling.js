/**
 * Centralized form error handling hook
 * Provides consistent error handling across all medical forms
 */

import { useState, useCallback } from 'react';
import { parseApiError, getFieldValidationErrors } from '../utils/errorHandling';
import logger from '../services/logger';

export const useFormErrorHandling = (componentName = 'UnknownForm') => {
  const [fieldErrors, setFieldErrors] = useState({});

  /**
   * Clear all field errors
   */
  const clearFieldErrors = useCallback(() => {
    setFieldErrors({});
  }, []);

  /**
   * Clear specific field error
   */
  const clearFieldError = useCallback((fieldName) => {
    setFieldErrors(prev => {
      if (prev[fieldName]) {
        logger.debug(`${componentName} field error cleared`, {
          field: fieldName,
          component: componentName
        });
      }
      const updated = { ...prev };
      delete updated[fieldName];
      return updated;
    });
  }, [componentName]);

  /**
   * Handle form submission errors with enhanced parsing
   * @param {Object} error - Error object from API
   * @param {Object} formData - Form data that was being submitted
   * @param {Function} setError - Function to set general error message
   * @returns {boolean} - Returns true if errors were handled, false if no errors
   */
  const handleSubmissionError = useCallback((error, formData, setError) => {
    if (!error) return false;

    logger.error(`${componentName} submission failed`, {
      error: error.message || error,
      errorType: error.constructor?.name,
      statusCode: error.status || error.response?.status,
      errorDetails: error.response?.data || error.detail,
      formData,
      component: componentName,
      timestamp: new Date().toISOString()
    });

    // Parse the error for field-specific feedback
    const parsed = parseApiError(error);
    
    // Set field-specific errors
    const fieldErrorCount = Object.keys(parsed.fieldErrors || {}).length;
    setFieldErrors(parsed.fieldErrors || {});
    
    if (fieldErrorCount > 0) {
      logger.debug(`${componentName} field errors identified`, {
        fieldErrorCount,
        fields: Object.keys(parsed.fieldErrors),
        component: componentName
      });
    }
    
    // Create user-friendly general message
    let message = '';
    
    if (parsed.general) {
      message += parsed.general;
    }
    
    const fieldCount = Object.keys(parsed.fieldErrors || {}).length;
    if (fieldCount > 0) {
      if (message) message += '\n\n';
      message += `Please fix the following ${fieldCount === 1 ? 'issue' : 'issues'}:\n`;
      
      Object.entries(parsed.fieldErrors).forEach(([field, fieldMessage], index) => {
        const fieldName = getFieldDisplayName(field);
        message += `• ${fieldName}: ${fieldMessage}`;
        if (index < fieldCount - 1) message += '\n';
      });
    }
    
    if (parsed.suggestions && parsed.suggestions.length > 0) {
      if (message) message += '\n\n';
      message += 'Helpful tips:\n';
      parsed.suggestions.forEach((suggestion, index) => {
        message += `• ${suggestion}`;
        if (index < parsed.suggestions.length - 1) message += '\n';
      });
    }
    
    // Set the comprehensive error message
    setError(message);
    
    return true;
  }, [componentName]);

  /**
   * Handle input change and clear related field error
   * @param {Function} originalOnChange - Original onChange handler
   * @returns {Function} - Enhanced onChange handler that clears field errors on input
   */
  const createChangeHandler = useCallback((originalOnChange) => {
    return (e) => {
      // Call original handler first
      if (originalOnChange) {
        originalOnChange(e);
      }
      
      // Clear field error when user starts typing
      // Works with synthetic events created by useFormHandlers
      const fieldName = e?.target?.name;
      if (fieldName && fieldErrors[fieldName]) {
        clearFieldError(fieldName);
      }
    };
  }, [fieldErrors, clearFieldError]);

  return {
    fieldErrors,
    clearFieldErrors,
    clearFieldError,
    handleSubmissionError,
    createChangeHandler,
    hasFieldErrors: Object.keys(fieldErrors).length > 0
  };
};

/**
 * Get display name for form fields
 * @param {string} fieldName - Internal field name
 * @returns {string} - User-friendly field name
 */
const getFieldDisplayName = (fieldName) => {
  const fieldNames = {
    // Common fields
    name: 'Name',
    email: 'Email',
    phone: 'Phone',
    notes: 'Notes',
    
    // Family member fields
    relationship: 'Relationship',
    gender: 'Gender',
    birth_year: 'Birth Year',
    death_year: 'Death Year',
    is_deceased: 'Deceased Status',
    patient_id: 'Patient Information',
    
    // Condition fields
    diagnosis: 'Diagnosis',
    condition_name: 'Condition Name',
    condition_type: 'Condition Type',
    severity: 'Severity',
    status: 'Status',
    onset_date: 'Onset Date',
    end_date: 'End Date',
    icd10_code: 'ICD-10 Code',
    snomed_code: 'SNOMED Code',
    
    // Medication fields
    medication_name: 'Medication Name',
    dosage: 'Dosage',
    frequency: 'Frequency',
    route: 'Route',
    indication: 'Indication',
    effective_period_start: 'Start Date',
    effective_period_end: 'End Date',
    practitioner_id: 'Prescribing Provider',
    pharmacy_id: 'Pharmacy',
    
    // Emergency contact fields
    phone_number: 'Phone Number',
    secondary_phone: 'Secondary Phone',
    address: 'Address',
    is_primary: 'Primary Contact',
    is_active: 'Active Contact',
    
    // Add more as needed...
  };
  
  return fieldNames[fieldName] || fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};