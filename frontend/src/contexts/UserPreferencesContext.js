import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  getUserPreferences,
  updateUserPreferences,
} from '../services/api/userPreferencesApi';
import { useAuth } from './AuthContext';
import frontendLogger from '../services/frontendLogger';
import { PAPERLESS_SETTING_DEFAULTS } from '../constants/paperlessSettings';

/**
 * User Preferences Context
 * Provides user preferences (including unit system) throughout the app
 */

const UserPreferencesContext = createContext();

export const useUserPreferences = () => {
  const context = useContext(UserPreferencesContext);
  if (!context) {
    throw new Error(
      'useUserPreferences must be used within a UserPreferencesProvider'
    );
  }
  return context;
};

export const UserPreferencesProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user preferences when authenticated user changes
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        setError(null);
        const userPrefs = await getUserPreferences();
        setPreferences(userPrefs);

        frontendLogger.logInfo('User preferences loaded', {
          unitSystem: userPrefs.unit_system,
          paperlessEnabled: userPrefs.paperless_enabled,
          userId: user?.id,
          component: 'UserPreferencesContext',
        });
      } catch (err) {
        const errorMessage = err.message || 'Failed to load user preferences';
        setError(errorMessage);

        // Set default preferences on error
        const defaultPrefs = {
          unit_system: 'imperial',
          ...PAPERLESS_SETTING_DEFAULTS,
          // Override the sync tags default for this context
          paperless_sync_tags: true,
        };
        setPreferences(defaultPrefs);

        frontendLogger.logError(
          'Failed to load user preferences, using defaults',
          {
            error: errorMessage,
            defaultPreferences: defaultPrefs,
            userId: user?.id,
            component: 'UserPreferencesContext',
          }
        );
      } finally {
        setLoading(false);
      }
    };

    // Only load preferences if user is authenticated
    if (isAuthenticated && user) {
      // Always fetch fresh preferences from database on login
      loadPreferences();
    } else {
      // On logout, don't clear preferences - just stop loading
      setLoading(false);
      setError(null);

      frontendLogger.logInfo('User logged out, preferences preserved for UI consistency', {
        component: 'UserPreferencesContext',
      });
    }
  }, [isAuthenticated, user?.id]); // Depend on authentication state and user ID

  // Function to update preferences and save to server
  const updatePreferences = async newPreferences => {
    try {
      // Save to server first
      const updatedPreferences = await updateUserPreferences(newPreferences);

      // Then update local state with server response
      setPreferences(prev => ({
        ...prev,
        ...updatedPreferences,
      }));

      frontendLogger.logInfo('User preferences updated and saved', {
        updatedFields: Object.keys(newPreferences),
        component: 'UserPreferencesContext',
      });

      return updatedPreferences;
    } catch (err) {
      const errorMessage = err.message || 'Failed to save user preferences';
      setError(errorMessage);

      frontendLogger.logError('Failed to save user preferences', {
        error: errorMessage,
        updatedFields: Object.keys(newPreferences),
        component: 'UserPreferencesContext',
      });

      throw err;
    }
  };

  // Function to update local preferences only (for internal use)
  const updateLocalPreferences = newPreferences => {
    setPreferences(prev => ({
      ...prev,
      ...newPreferences,
    }));
  };

  // Function to refresh preferences from server
  const refreshPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      const userPrefs = await getUserPreferences();
      setPreferences(userPrefs);
      return userPrefs;
    } catch (err) {
      const errorMessage = err.message || 'Failed to refresh user preferences';
      setError(errorMessage);
      frontendLogger.logError('Failed to refresh user preferences', {
        error: errorMessage,
        component: 'UserPreferencesContext',
      });
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const value = {
    preferences,
    loading,
    error,
    updatePreferences, // Now saves to server automatically
    updateLocalPreferences, // Local state update only (for backwards compatibility)
    refreshPreferences,
    // Convenience getters
    unitSystem: preferences?.unit_system || 'imperial',
    isMetric: preferences?.unit_system === 'metric',
    isImperial: preferences?.unit_system === 'imperial',
  };

  return (
    <UserPreferencesContext.Provider value={value}>
      {children}
    </UserPreferencesContext.Provider>
  );
};

export default UserPreferencesContext;
