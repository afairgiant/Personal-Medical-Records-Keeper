import { useState, useEffect, useCallback, useRef } from 'react';
import { useApi } from './useApi';
import { apiService } from '../services/api';
import { useCurrentPatient } from './useGlobalData';

export const useMedicalData = config => {
  const {
    entityName,
    apiMethodsConfig,
    requiresPatient = true,
    loadFilesCounts = false,
  } = config;

  const [items, setItems] = useState([]);
  const [filesCounts, setFilesCounts] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const isInitialized = useRef(false);
  const abortControllerRef = useRef(null);

  // Use global patient context instead of managing patient state locally
  const { patient: currentPatient, loading: patientLoading } =
    useCurrentPatient();
  const currentPatientRef = useRef(currentPatient);

  // Keep ref in sync with global patient state and reset initialization when patient changes
  useEffect(() => {
    currentPatientRef.current = currentPatient;
    // Reset initialization flag when patient changes to allow re-initialization
    if (currentPatient?.id) {
      isInitialized.current = false;
    }
  }, [currentPatient?.id]);

  const { loading, error, execute, clearError, setError, cleanup } = useApi();

  // Create item
  const createItem = useCallback(
    async data => {
      console.log(`🏗️ Creating ${entityName} with data:`, data);

      const result = await execute(
        async signal => {
          console.log(`📡 Calling API create method for ${entityName}`);
          return await apiMethodsConfig.create(data, signal);
        },
        { errorMessage: `Failed to create ${entityName}` }
      );

      console.log(`✅ Create ${entityName} result:`, result);

      if (result) {
        setSuccessMessage(`${entityName} created successfully!`);
        setTimeout(() => setSuccessMessage(''), 3000);
        return result;
      }
      return false;
    },
    [execute, apiMethodsConfig, entityName]
  );

  // Update item
  const updateItem = useCallback(
    async (id, data) => {
      const result = await execute(
        async signal => await apiMethodsConfig.update(id, data, signal),
        { errorMessage: `Failed to update ${entityName}` }
      );

      if (result) {
        setSuccessMessage(`${entityName} updated successfully!`);
        setTimeout(() => setSuccessMessage(''), 3000);
        return result;
      }
      return false;
    },
    [execute, apiMethodsConfig, entityName]
  );

  // Delete item
  const deleteItem = useCallback(
    async id => {
      if (
        !window.confirm(`Are you sure you want to delete this ${entityName}?`)
      ) {
        return false;
      }

      const result = await execute(
        async signal => await apiMethodsConfig.delete(id, signal),
        { errorMessage: `Failed to delete ${entityName}` }
      );

      if (result) {
        setSuccessMessage(`${entityName} deleted successfully!`);
        setTimeout(() => setSuccessMessage(''), 3000);
        return result;
      }
      return false;
    },
    [execute, apiMethodsConfig, entityName]
  ); // Store stable references to prevent dependency changes
  const configRef = useRef({
    entityName,
    apiMethodsConfig,
    requiresPatient,
    loadFilesCounts,
  });

  // Update config ref when props change
  useEffect(() => {
    configRef.current = {
      entityName,
      apiMethodsConfig,
      requiresPatient,
      loadFilesCounts,
    };
  }, [entityName, apiMethodsConfig, requiresPatient, loadFilesCounts]);

  // Initialize data - run once on mount
  useEffect(() => {
    let isMounted = true;
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const initializeData = async () => {
      if (isInitialized.current || !isMounted) return;

      console.log('Initializing data...');
      isInitialized.current = true;

      const config = configRef.current;

      try {
        // Wait for patient data to be available if required
        if (config.requiresPatient) {
          if (!currentPatient?.id) {
            console.warn('No patient data available yet, waiting...');
            return;
          }
        }

        if (!isMounted) return;

        let data = [];
        if (config.requiresPatient && currentPatient?.id) {
          data = await config.apiMethodsConfig.getByPatient(
            currentPatient.id,
            abortController.signal
          );
        } else if (!config.requiresPatient) {
          data = await config.apiMethodsConfig.getAll(abortController.signal);
        }

        if (data && isMounted) {
          // Extract data array from API response if it's wrapped in a response object
          const extractedData = data?.data || data;
          setItems(Array.isArray(extractedData) ? extractedData : []);

          if (
            config.loadFilesCounts &&
            extractedData.length <= 20 &&
            config.apiMethodsConfig.getFiles
          ) {
            const counts = {};
            for (const item of extractedData) {
              try {
                const files = await config.apiMethodsConfig.getFiles(
                  item.id,
                  abortController.signal
                );
                counts[item.id] = files?.length || 0;
              } catch (error) {
                if (error.name !== 'AbortError') {
                  console.warn(
                    `Failed to load file count for ${config.entityName} ${item.id}:`,
                    error
                  );
                }
                counts[item.id] = 0;
              }
              await new Promise(resolve => setTimeout(resolve, 100));
            }

            if (isMounted) {
              setFilesCounts(counts);
            }
          }
        }
      } catch (error) {
        if (error.name !== 'AbortError' && isMounted) {
          setError(
            `Failed to load ${config.entityName} data: ${error.message}`
          );
        }
      }
    };

    initializeData();

    return () => {
      isMounted = false;
      isInitialized.current = false;
      abortController.abort();
      cleanup();
    };
  }, [setError, cleanup, currentPatient?.id]); // Include currentPatient.id to reinitialize when patient loads
  // Refresh data function that uses execute wrapper
  const refreshData = useCallback(async () => {
    const config = configRef.current;
    const result = await execute(
      async signal => {
        let data = [];
        if (config.requiresPatient && currentPatientRef.current?.id) {
          data = await config.apiMethodsConfig.getByPatient(
            currentPatientRef.current.id,
            signal
          );
        } else if (!config.requiresPatient) {
          data = await config.apiMethodsConfig.getAll(signal);
        }

        if (data) {
          // Extract data array from API response if it's wrapped in a response object
          const extractedData = data?.data || data;
          setItems(Array.isArray(extractedData) ? extractedData : []);

          if (
            config.loadFilesCounts &&
            extractedData.length <= 20 &&
            config.apiMethodsConfig.getFiles
          ) {
            const counts = {};
            for (const item of extractedData) {
              try {
                const files = await config.apiMethodsConfig.getFiles(
                  item.id,
                  signal
                );
                counts[item.id] = files?.length || 0;
              } catch (error) {
                if (error.name !== 'AbortError') {
                  console.warn(
                    `Failed to load file count for ${config.entityName} ${item.id}:`,
                    error
                  );
                }
                counts[item.id] = 0;
              }
              await new Promise(resolve => setTimeout(resolve, 100));
            }
            setFilesCounts(counts);
          }

          return extractedData;
        }
        return [];
      },
      { errorMessage: `Failed to refresh ${config.entityName} data` }
    );
    return result;
  }, [execute]);

  return {
    // Data
    items,
    currentPatient,
    filesCounts,

    // State
    loading: loading || patientLoading, // Combine API loading and patient loading
    error,
    successMessage,

    // Actions
    createItem,
    updateItem,
    deleteItem,
    refreshData,
    clearError,

    // Utilities
    setSuccessMessage,
    setError,
  };
};
