import { useState, useCallback, useRef } from 'react';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastErrorObject, setLastErrorObject] = useState(null);
  const abortControllerRef = useRef(null);

  const execute = useCallback(async (apiCall, options = {}) => {
    // Cancel any existing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      setLoading(true);
      setError(null);
      setLastErrorObject(null);

      const result = await apiCall(controller.signal);

      // Check if request was cancelled
      if (controller.signal.aborted) {
        return null;
      }

      return result;
    } catch (err) {
      // Don't show errors if request was cancelled
      if (err.name !== 'AbortError' && !controller.signal.aborted) {
        const errorMessage =
          options.errorMessage || err.message || 'An error occurred';
        setError(errorMessage);
        setLastErrorObject(err); // Store the original error object
        console.error('API Error:', err);
      }
      return null;
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setLastErrorObject(null);
  }, []);

  const setErrorMessage = useCallback(message => {
    setError(message);
  }, []);

  const cleanup = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    loading,
    error,
    lastErrorObject,
    execute,
    clearError,
    setError: setErrorMessage,
    cleanup,
  };
};

/**
 * Hook for form state management with validation
 * @param {Object} initialValues - Initial form values
 * @param {Function} validationSchema - Validation function
 * @returns {Object} - Form state and handlers
 */
export const useForm = (initialValues, validationSchema) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const handleChange = e => {
    const { name, value } = e.target;
    setValues(prev => ({ ...prev, [name]: value }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleBlur = e => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));

    if (validationSchema) {
      const fieldErrors = validationSchema(values);
      setErrors(prev => ({ ...prev, [name]: fieldErrors[name] || '' }));
    }
  };

  const validate = () => {
    if (!validationSchema) return true;

    const validationErrors = validationSchema(values);
    setErrors(validationErrors);

    return Object.keys(validationErrors).length === 0;
  };

  const reset = () => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  };

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validate,
    reset,
    setValues,
  };
};
