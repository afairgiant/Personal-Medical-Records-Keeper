/**
 * Utility functions for handling API errors and providing user-friendly messages
 */

/**
 * Parse API errors and convert them to user-friendly messages
 * @param {Object} error - Error object from API (can be any status code)
 * @returns {Object} - Parsed error with field-specific messages
 */
export const parseApiError = (error) => {
  const result = {
    general: '',
    fieldErrors: {},
    suggestions: [],
    statusCode: null
  };

  if (!error) {
    result.general = 'An unexpected error occurred. Please try again.';
    return result;
  }

  // Log the raw error for debugging
  console.debug('Parsing API error:', {
    error,
    errorMessage: error.message,
    errorType: error.constructor?.name,
    statusCode: error.status || error.response?.status
  });

  // Extract status code if available
  if (error.response?.status) {
    result.statusCode = error.response.status;
  } else if (error.status) {
    result.statusCode = error.status;
  }

  // Get error message from various possible locations
  const errorMessage = error.message || 
                      error.detail || 
                      error.response?.data?.detail || 
                      error.response?.data?.message ||
                      error.data?.detail ||
                      error.data?.message ||
                      'Unknown error occurred';

  // Handle different types of errors based on status code
  if (result.statusCode) {
    switch (result.statusCode) {
      case 400:
        return parseBadRequestError(errorMessage, result);
      case 401:
        return parseAuthError(errorMessage, result);
      case 403:
        return parseForbiddenError(errorMessage, result);
      case 404:
        return parseNotFoundError(errorMessage, result);
      case 409:
        return parseConflictError(errorMessage, result);
      case 422:
        return parseValidationErrors(errorMessage, result);
      case 429:
        return parseRateLimitError(errorMessage, result);
      case 500:
      case 502:
      case 503:
      case 504:
        return parseServerError(errorMessage, result);
      default:
        return parseGenericError(errorMessage, result);
    }
  }

  // If no status code, try to parse as validation error
  return parseValidationErrors(errorMessage, result);
};

/**
 * Parse 400 Bad Request errors
 */
const parseBadRequestError = (errorMessage, result) => {
  result.general = 'Invalid request data provided.';
  result.suggestions.push('Please check that all required fields are filled correctly.');
  result.suggestions.push('Make sure dates are in the correct format.');
  
  if (errorMessage.toLowerCase().includes('invalid')) {
    result.general = `Invalid data: ${errorMessage}`;
  }
  
  return result;
};

/**
 * Parse 401 Authentication errors
 */
const parseAuthError = (errorMessage, result) => {
  result.general = 'Authentication failed. Please log in again.';
  result.suggestions.push('Your session may have expired.');
  result.suggestions.push('Try refreshing the page and logging in again.');
  return result;
};

/**
 * Parse 403 Forbidden errors
 */
const parseForbiddenError = (errorMessage, result) => {
  result.general = 'You do not have permission to perform this action.';
  result.suggestions.push('Contact your administrator if you believe you should have access.');
  return result;
};

/**
 * Parse 404 Not Found errors
 */
const parseNotFoundError = (errorMessage, result) => {
  result.general = 'The requested resource was not found.';
  result.suggestions.push('The item may have been deleted or moved.');
  result.suggestions.push('Try refreshing the page or going back to the main list.');
  return result;
};

/**
 * Parse 409 Conflict errors
 */
const parseConflictError = (errorMessage, result) => {
  result.general = 'A conflict occurred with existing data.';
  result.suggestions.push('This item may already exist or conflict with another record.');
  result.suggestions.push('Check for duplicate entries.');
  
  if (errorMessage.toLowerCase().includes('duplicate') || errorMessage.toLowerCase().includes('exists')) {
    result.general = 'This record already exists or conflicts with an existing one.';
  }
  
  return result;
};

/**
 * Parse 422 Validation errors and other validation-related errors
 */
const parseValidationErrors = (errorMessage, result) => {
  // Handle FastAPI validation errors (array format)
  if (errorMessage.includes('Validation errors:')) {
    const validationPart = errorMessage.replace('Validation errors: ', '');
    const errors = validationPart.split(', ');
    
    errors.forEach(err => {
      const fieldError = parseFieldValidationError(err);
      if (fieldError.field) {
        result.fieldErrors[fieldError.field] = fieldError.message;
      } else {
        result.general += (result.general ? ' ' : '') + fieldError.message;
      }
    });
  } 
  // Parse specific validation patterns
  else {
    parseSpecificValidationErrors(errorMessage, result);
  }

  // Add general suggestions if no specific ones were provided
  if (Object.keys(result.fieldErrors).length === 0 && result.suggestions.length === 0) {
    result.suggestions = ['Please check your input and try again.', 'Make sure all required fields are filled correctly.'];
  }

  return result;
};

/**
 * Parse 429 Rate Limit errors
 */
const parseRateLimitError = (errorMessage, result) => {
  result.general = 'Too many requests. Please wait before trying again.';
  result.suggestions.push('Wait a few moments before submitting again.');
  result.suggestions.push('Avoid clicking the submit button multiple times.');
  return result;
};

/**
 * Parse 500+ Server errors
 */
const parseServerError = (errorMessage, result) => {
  result.general = 'A server error occurred. Please try again later.';
  result.suggestions.push('This is likely a temporary issue.');
  result.suggestions.push('Try again in a few minutes.');
  result.suggestions.push('Contact support if the problem persists.');
  return result;
};

/**
 * Parse generic/unknown errors
 */
const parseGenericError = (errorMessage, result) => {
  result.general = errorMessage || 'An unexpected error occurred.';
  result.suggestions.push('Please try again.');
  result.suggestions.push('If the problem persists, contact support.');
  return result;
};

/**
 * Parse specific validation error patterns and provide actionable feedback
 * @param {string} errorMessage - Error message to parse
 * @param {Object} result - Result object to populate
 */
const parseSpecificValidationErrors = (errorMessage, result) => {
  const validationPatterns = [
    // Family member specific errors
    {
      pattern: /Relationship must be one of:/i,
      fieldErrors: { relationship: 'Please select a valid relationship from the dropdown menu.' },
      suggestions: ['Choose from: Father, Mother, Brother, Sister, Uncle, Aunt, Cousin, or Other.', 'You cannot type custom relationships - only predefined options are allowed.']
    },
    {
      pattern: /Gender must be one of:/i,
      fieldErrors: { gender: 'Please select a valid gender option.' },
      suggestions: ['Choose Male, Female, or Other from the dropdown.', 'Leave blank if you prefer not to specify.']
    },
    {
      pattern: /Death year cannot be before birth year/i,
      fieldErrors: { 
        death_year: 'Death year must be after the birth year.',
        birth_year: 'Check that the birth year is correct.'
      },
      suggestions: ['Verify both birth year and death year are accurate.', 'Death year should be greater than birth year.']
    },
    {
      pattern: /Death year can only be set if family member is deceased/i,
      fieldErrors: { 
        death_year: 'Remove the death year or mark the person as deceased.',
        is_deceased: 'Check "Deceased" if this family member has passed away.'
      },
      suggestions: ['Either clear the death year field or check the "Deceased" checkbox.']
    },
    {
      pattern: /If death year is provided, family member must be marked as deceased/i,
      fieldErrors: { 
        is_deceased: 'Check "Deceased" when entering a death year.'
      },
      suggestions: ['When you enter a death year, you must also check the "Deceased" checkbox.']
    },
    
    // General validation patterns
    {
      pattern: /field required|is required/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'name';
        return { [field]: `${getFieldDisplayName(field)} is required.` };
      },
      suggestions: ['Fill in all required fields marked with an asterisk (*).']
    },
    {
      pattern: /min_length|at least (\d+) characters/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'name';
        const minLength = msg.match(/(\d+)/)?.[1] || '1';
        return { [field]: `${getFieldDisplayName(field)} must be at least ${minLength} character${minLength > 1 ? 's' : ''} long.` };
      },
      suggestions: ['Enter a longer value for this field.']
    },
    {
      pattern: /max_length|at most (\d+) characters/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'notes';
        const maxLength = msg.match(/(\d+)/)?.[1] || '100';
        return { [field]: `${getFieldDisplayName(field)} cannot exceed ${maxLength} characters.` };
      },
      suggestions: ['Shorten the text to fit within the character limit.']
    },
    {
      pattern: /ensure this value is greater than or equal to (\d+)|ge=(\d+)/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'birth_year';
        const minValue = msg.match(/(\d+)/)?.[1] || '1900';
        return { [field]: `${getFieldDisplayName(field)} must be ${minValue} or greater.` };
      },
      suggestions: ['Enter a valid year (1900 or later).']
    },
    {
      pattern: /ensure this value is less than or equal to (\d+)|le=(\d+)/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'birth_year';
        const maxValue = msg.match(/(\d+)/)?.[1] || '2030';
        return { [field]: `${getFieldDisplayName(field)} cannot be greater than ${maxValue}.` };
      },
      suggestions: ['Enter a realistic year (not in the distant future).']
    },
    {
      pattern: /not a valid integer|invalid number/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'birth_year';
        return { [field]: `${getFieldDisplayName(field)} must be a valid number.` };
      },
      suggestions: ['Enter only numbers for year fields.', 'Remove any letters or special characters.']
    },
    {
      pattern: /value is not a valid enumeration member/i,
      fieldErrors: (msg) => {
        const field = extractFieldFromError(msg) || 'relationship';
        return { [field]: `Please select a valid option for ${getFieldDisplayName(field)}.` };
      },
      suggestions: ['Choose from the available dropdown options.', 'Custom values are not allowed for this field.']
    }
  ];

  // Try to match against known patterns
  for (const { pattern, fieldErrors, suggestions } of validationPatterns) {
    if (pattern.test(errorMessage)) {
      console.debug('Validation pattern matched:', {
        pattern: pattern.toString(),
        errorMessage,
        patternType: 'specific_validation'
      });
      
      // Handle field errors (can be function or object)
      const errors = typeof fieldErrors === 'function' ? fieldErrors(errorMessage) : fieldErrors;
      Object.assign(result.fieldErrors, errors);
      
      // Add suggestions
      if (suggestions) {
        result.suggestions.push(...suggestions);
      }
      return;
    }
  }

  // If no specific pattern matched, use generic handling
  result.general = errorMessage;
};

/**
 * Parse individual field validation error
 * @param {string} errorString - Single validation error string
 * @returns {Object} - Field and message
 */
const parseFieldValidationError = (errorString) => {
  // Common patterns in FastAPI validation errors
  const patterns = [
    { regex: /field required/, field: null, message: 'This field is required.' },
    { regex: /ensure this value has at least (\d+) characters/, field: null, message: 'This field is too short.' },
    { regex: /ensure this value has at most (\d+) characters/, field: null, message: 'This field is too long.' },
    { regex: /value is not a valid enumeration member/, field: null, message: 'Please select a valid option.' },
    { regex: /not a valid integer/, field: null, message: 'Please enter a valid number.' },
    { regex: /ensure this value is greater than or equal to (\d+)/, field: null, message: 'Value is too small.' },
    { regex: /ensure this value is less than or equal to (\d+)/, field: null, message: 'Value is too large.' },
  ];

  for (const pattern of patterns) {
    if (pattern.regex.test(errorString)) {
      return {
        field: pattern.field,
        message: pattern.message
      };
    }
  }

  return {
    field: null,
    message: errorString
  };
};

/**
 * Extract field name from error message
 * @param {string} errorMessage - Error message
 * @returns {string} - Field name or empty string
 */
const extractFieldFromError = (errorMessage) => {
  // Try to extract field name from common error patterns
  const fieldPatterns = [
    /field (\w+)/,
    /(\w+) field/,
    /invalid (\w+)/
  ];

  for (const pattern of fieldPatterns) {
    const match = errorMessage.match(pattern);
    if (match) {
      return match[1];
    }
  }

  return '';
};


/**
 * Get field-specific validation errors for forms (for backward compatibility)
 * @param {Object} error - Error object from API
 * @returns {Object} - Object with field names as keys and error messages as values
 */
export const getFieldValidationErrors = (error) => {
  const parsed = parseApiError(error);
  return parsed.fieldErrors;
};

// Keep the old function name for backward compatibility
export const parseValidationError = parseApiError;