import React from 'react';
import {
  Modal,
  TextInput,
  Select,
  Textarea,
  NumberInput,
  Button,
  Group,
  Stack,
  Grid,
  Text,
  Rating,
  Anchor,
  Checkbox,
  Divider,
  Alert,
} from '@mantine/core';
import { IconAlertTriangle } from '@tabler/icons-react';
import { DateInput } from '@mantine/dates';
import { useFormHandlers } from '../../hooks/useFormHandlers';

/**
 * BaseMedicalForm - Reusable form component for medical data entry
 * 
 * This component abstracts common medical form patterns including:
 * - Modal wrapper with consistent styling
 * - Dynamic field rendering based on configuration
 * - Standardized form handlers and validation
 * - Consistent button layout and styling
 */
const BaseMedicalForm = ({
  // Modal props
  isOpen,
  onClose,
  title,
  
  // Form data and handlers
  formData,
  onInputChange,
  onSubmit,
  
  // Field configuration
  fields = [],
  
  // Dynamic options for select fields
  dynamicOptions = {},
  
  // Loading states for dynamic options
  loadingStates = {},

  // Form state
  editingItem = null,
  isLoading = false,
  
  // Error handling
  fieldErrors = {},
  
  // Custom content
  children,
  
  // Button customization
  submitButtonText,
  submitButtonColor,
  
  // Modal customization
  modalSize = "lg",
}) => {
  const { 
    handleTextInputChange, 
    handleSelectChange, 
    handleDateChange, 
    handleNumberChange 
  } = useFormHandlers(onInputChange);

  // Handle Rating onChange (receives value directly)
  const handleRatingChange = (field) => (value) => {
    const syntheticEvent = {
      target: {
        name: field,
        value: value || '',
      },
    };
    onInputChange(syntheticEvent);
  };

  // Handle Checkbox onChange
  const handleCheckboxChange = (field) => (event) => {
    const syntheticEvent = {
      target: {
        name: field,
        value: event.currentTarget.checked,
        type: 'checkbox',
        checked: event.currentTarget.checked,
      },
    };
    onInputChange(syntheticEvent);
  };

  const handleSubmit = e => {
    e.preventDefault();
    onSubmit(e);
  };

  // Render individual form field based on configuration
  const renderField = (fieldConfig) => {
    const {
      name,
      type,
      label,
      placeholder,
      required = false,
      description,
      options = [],
      dynamicOptions: dynamicOptionsKey,
      searchable = false,
      clearable = false,
      minRows,
      maxRows,
      maxDate,
      minDate,
      maxLength,
      min,
      max,
      maxDropdownHeight,
    } = fieldConfig;

    // Get dynamic options if specified
    const selectOptions = dynamicOptionsKey 
      ? dynamicOptions[dynamicOptionsKey] || []
      : options;
     
    // Check if this dynamic option is loading
    const isFieldLoading = dynamicOptionsKey && loadingStates[dynamicOptionsKey];


    // Base field props with smart error handling
    // Integrates our custom validation errors with Mantine's built-in error display
    // without conflicting with HTML5 validation or Mantine's own validation
    const customError = fieldErrors[name] || null;
    
    // Don't override HTML5 email validation with generic messages
    // This prevents showing confusing duplicate error messages
    const shouldShowCustomError = customError && !(
      type === 'email' && 
      customError.includes('valid') && 
      !customError.includes('required')
    );
    
    const baseProps = {
      label,
      placeholder,
      description,
      required,
      withAsterisk: required,
      value: formData[name] || '',
      maxLength,
      error: shouldShowCustomError ? customError : null,
    };

    switch (type) {
      case 'text':
      case 'email':
        return (
          <TextInput
            {...baseProps}
            onChange={handleTextInputChange(name)}
            type={type === 'email' ? 'email' : 'text'}
          />
        );

      case 'textarea':
        return (
          <Textarea
            {...baseProps}
            onChange={handleTextInputChange(name)}
            minRows={minRows}
            maxRows={maxRows}
          />
        );

      case 'select':
        return (
          <Select
            {...baseProps}
            data={selectOptions}
            onChange={handleSelectChange(name)}
            searchable={searchable}
            clearable={clearable}
            maxDropdownHeight={maxDropdownHeight}

            disabled={isFieldLoading}
            placeholder={isFieldLoading ? `Loading ${dynamicOptionsKey}...` : placeholder}

          />
        );

      case 'number':
        // NumberInput needs special value handling
        const numberValue = formData[name] !== undefined && formData[name] !== null && formData[name] !== '' ? Number(formData[name]) : '';
        return (
          <NumberInput
            label={label}
            placeholder={placeholder}
            description={description}
            required={required}
            withAsterisk={required}
            error={shouldShowCustomError ? customError : null}
            maxLength={maxLength}
            value={numberValue}
            onChange={handleNumberChange(name)}
            min={min}
            max={max}
          />
        );

      case 'date':

        // Handle dynamic minDate for any end date field based on corresponding start date
        let dynamicMinDate = minDate;
        
        // Support multiple start/end date patterns with robust field name derivation
        if (name === 'end_date' && formData.onset_date) {
          dynamicMinDate = new Date(formData.onset_date);
        } else if (name === 'end_date' && formData.start_date) {
          dynamicMinDate = new Date(formData.start_date);
        } else {
          // Generic pattern: derive start field name from end field name
          let startFieldName = null;
          
          // Pattern 1: ends with '_end_date' -> replace with '_start_date'
          if (name.endsWith('_end_date')) {
            startFieldName = name.substring(0, name.length - '_end_date'.length) + '_start_date';
          }
          // Pattern 2: ends with '_end' -> replace with '_start'  
          else if (name.endsWith('_end') && name.includes('date')) {
            startFieldName = name.substring(0, name.length - '_end'.length) + '_start';
          }
          // Pattern 3: contains 'end_date' -> replace with 'start_date'
          else if (name.includes('end_date')) {
            startFieldName = name.replace(/end_date/g, 'start_date');
          }
          // Pattern 4: for fields like 'completion_end_date' -> 'completion_start_date'
          else if (name.includes('_end_') && name.includes('date')) {
            startFieldName = name.replace(/_end_/g, '_start_');
          }
          
          // Apply the derived start field if it exists in formData
          if (startFieldName && formData[startFieldName]) {
            dynamicMinDate = new Date(formData[startFieldName]);
          }
        }
        
        // Handle dynamic maxDate - use current date if maxDate is a function
        const dynamicMaxDate = typeof maxDate === 'function' ? maxDate() : maxDate;

          
        return (
          <DateInput
            {...baseProps}
            value={formData[name] ? new Date(formData[name]) : null}
            onChange={handleDateChange(name)}
            firstDayOfWeek={0}
            clearable
            maxDate={dynamicMaxDate}

            minDate={dynamicMinDate}
          />
        );

      case 'rating':
        const hasRatingError = shouldShowCustomError ? customError : null;
        return (
          <div>
            <Text 
              size="sm" 
              fw={500} 
              style={{ 
                marginBottom: '8px',
                color: hasRatingError ? 'var(--mantine-color-error)' : undefined 
              }}
            >
              {label}
              {required && <span style={{ color: 'var(--mantine-color-error)' }}> *</span>}
            </Text>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Rating
                value={formData[name] ? parseFloat(formData[name]) : 0}
                onChange={handleRatingChange(name)}
                fractions={2}
                size="lg"
              />
              <Text size="sm" c="dimmed">
                {formData[name] ? `${formData[name]}/5 stars` : 'No rating'}
              </Text>
            </div>
            {description && (
              <Text size="xs" c="dimmed" style={{ marginTop: '4px' }}>
                {description}
              </Text>
            )}
            {hasRatingError && (
              <Text size="xs" c="red" style={{ marginTop: '4px' }}>
                {hasRatingError}
              </Text>
            )}
          </div>
        );

      case 'checkbox':
        return (
          <Checkbox
            label={label}
            description={description}
            checked={!!formData[name]}
            onChange={handleCheckboxChange(name)}
            error={shouldShowCustomError ? customError : null}
          />
        );

      case 'divider':
        return (
          <div style={{ width: '100%' }}>
            <Divider my="md" />
            {label && (
              <Text size="sm" fw={600} mb="sm">
                {label}
              </Text>
            )}
          </div>
        );

      default:
        console.warn(`Unknown field type: ${type} for field: ${name}`);
        return null;
    }
  };

  // Group fields by row based on gridColumn values
  const groupFieldsIntoRows = (fields) => {
    const rows = [];
    let currentRow = [];
    let currentRowSpan = 0;

    fields.forEach((field) => {
      const span = field.gridColumn || 12;
      
      // If adding this field would exceed 12 columns, start a new row
      if (currentRowSpan + span > 12) {
        if (currentRow.length > 0) {
          rows.push(currentRow);
        }
        currentRow = [field];
        currentRowSpan = span;
      } else {
        currentRow.push(field);
        currentRowSpan += span;
      }
    });

    // Add the last row if it has fields
    if (currentRow.length > 0) {
      rows.push(currentRow);
    }

    return rows;
  };

  const fieldRows = groupFieldsIntoRows(fields);

  // Determine submit button text
  const getSubmitButtonText = () => {
    if (submitButtonText) return submitButtonText;
    
    const entityName = title.replace('Add ', '').replace('Edit ', '');
    return editingItem ? `Update ${entityName}` : `Add ${entityName}`;
  };

  // Determine submit button color based on form data
  const getSubmitButtonColor = () => {
    if (submitButtonColor) return submitButtonColor;
    
    // Special case for allergy severity
    if (formData.severity === 'life-threatening') {
      return 'red';
    }
    
    return undefined;
  };

  return (
    <Modal
      opened={isOpen}
      onClose={onClose}
      title={
        <Text size="lg" fw={600}>
          {title}
        </Text>
      }
      size={modalSize}
      centered
      styles={{
        body: { padding: '1.5rem', paddingBottom: '2rem' },
        header: { paddingBottom: '1rem' },
      }}
      overflow="inside"
    >
      <form onSubmit={handleSubmit}>
        <Stack spacing="md">
          {/* Render form fields */}
          {fieldRows.map((row, rowIndex) => (
            <Grid key={rowIndex}>
              {row.map((field) => (
                <Grid.Col key={field.name} span={field.gridColumn || 12}>
                  {renderField(field)}
                </Grid.Col>
              ))}
            </Grid>
          ))}

          {/* Custom content section */}
          {children}

          {/* Form action buttons */}
          <Group justify="flex-end" mt="lg" mb="sm">
            <Button
              variant="subtle"
              onClick={onClose}
              disabled={isLoading}
              style={{
                minHeight: '42px',
                height: '42px',
                lineHeight: '1.2',
                padding: '8px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="filled"
              color={getSubmitButtonColor()}
              loading={isLoading}
              style={{
                minHeight: '42px',
                height: '42px',
                lineHeight: '1.2',
                padding: '8px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {getSubmitButtonText()}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
};

export default BaseMedicalForm;