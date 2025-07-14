import React from 'react';
import BaseMedicalForm from './BaseMedicalForm';
import { familyMemberFormFields } from '../../utils/medicalFormFields';
import logger from '../../services/logger';

const MantineFamilyMemberForm = ({
  isOpen,
  onClose,
  title,
  formData,
  onInputChange,
  onSubmit,
  editingMember = null,
  fieldErrors = {},
}) => {
  const dynamicOptions = {
    // Add any dynamic options for family members if needed
  };

  // Filter fields based on form state - only show death_year if is_deceased is true
  const filteredFields = familyMemberFormFields.filter(field => {
    if (field.name === 'death_year') {
      return formData && formData.is_deceased === true;
    }
    return true;
  });

  // Debug: Log the fields to check if they're properly loaded (only on component mount)
  React.useEffect(() => {
    logger.debug('Family member form fields loaded', {
      totalFields: familyMemberFormFields?.length,
      filteredFields: filteredFields?.length,
      component: 'MantineFamilyMemberForm',
      isDeceased: formData?.is_deceased
    });
  }, [filteredFields?.length, formData?.is_deceased]);

  // Safety check for fields
  if (!familyMemberFormFields || !Array.isArray(familyMemberFormFields)) {
    logger.error('Family member form fields are not properly defined', {
      component: 'MantineFamilyMemberForm',
      fieldsType: typeof familyMemberFormFields,
      fieldsValue: familyMemberFormFields
    });
    return null;
  }

  return (
    <BaseMedicalForm
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      formData={formData}
      onInputChange={onInputChange}
      onSubmit={onSubmit}
      editingItem={editingMember}
      fields={filteredFields}
      dynamicOptions={dynamicOptions}
      fieldErrors={fieldErrors}
    />
  );
};

export default MantineFamilyMemberForm;
