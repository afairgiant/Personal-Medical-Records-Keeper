import React from 'react';
import {
  Modal,
  Stack,
  Group,
  Button,
  TextInput,
  Textarea,
  Select,
  NumberInput,
  Alert,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { IconX } from '@tabler/icons-react';
import FormLoadingOverlay from '../../shared/FormLoadingOverlay';
import SubmitButton from '../../shared/SubmitButton';
import { useFormHandlers } from '../../../hooks/useFormHandlers';
import logger from '../../../services/logger';

const ImmunizationFormWrapper = ({
  isOpen,
  onClose,
  title,
  formData,
  onInputChange,
  onSubmit,
  editingImmunization,
  practitioners = [],
  isLoading,
  statusMessage,
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  const { handleDateChange } = useFormHandlers(onInputChange);

  const handleInputChange = (field, value) => {
    onInputChange({
      target: {
        name: field,
        value: value
      }
    });
  };

  if (!isOpen) return null;

  const practitionerOptions = practitioners.map(p => ({
    value: p.id.toString(),
    label: p.name
  }));

  return (
    <Modal
      opened={isOpen}
      onClose={onClose}
      title={title}
      size="lg"
      closeOnClickOutside={!isLoading}
      closeOnEscape={!isLoading}
    >
      <FormLoadingOverlay visible={isLoading} statusMessage={statusMessage} />

      <form onSubmit={handleSubmit}>
        <Stack gap="md">
          {/* Basic immunization information */}
          <TextInput
            label="Vaccine Name"
            name="vaccine_name"
            value={formData.vaccine_name || ''}
            onChange={(e) => onInputChange(e)}
            required
            placeholder="Enter vaccine name"
          />

          <DateInput
            label="Date Administered"
            name="date_administered"
            value={formData.date_administered ? new Date(formData.date_administered) : null}
            onChange={handleDateChange('date_administered')}
            placeholder="Select administration date"
          />

          <Group grow>
            <NumberInput
              label="Dose Number"
              name="dose_number"
              value={formData.dose_number || ''}
              onChange={(value) => handleInputChange('dose_number', value)}
              placeholder="Enter dose number"
              min={1}
              max={10}
            />

            <TextInput
              label="Lot Number"
              name="lot_number"
              value={formData.lot_number || ''}
              onChange={(e) => onInputChange(e)}
              placeholder="Enter lot number"
            />
          </Group>

          <TextInput
            label="Manufacturer"
            name="manufacturer"
            value={formData.manufacturer || ''}
            onChange={(e) => onInputChange(e)}
            placeholder="Enter manufacturer"
          />

          <Group grow>
            <Select
              label="Administration Site"
              name="site"
              value={formData.site || ''}
              onChange={(value) => handleInputChange('site', value)}
              data={[
                { value: 'left_arm', label: 'Left Arm' },
                { value: 'right_arm', label: 'Right Arm' },
                { value: 'left_thigh', label: 'Left Thigh' },
                { value: 'right_thigh', label: 'Right Thigh' },
                { value: 'left_deltoid', label: 'Left Deltoid' },
                { value: 'right_deltoid', label: 'Right Deltoid' },
                { value: 'oral', label: 'Oral' },
                { value: 'nasal', label: 'Nasal' },
              ]}
              placeholder="Select administration site"
              clearable
              searchable
            />

            <Select
              label="Administration Route"
              name="route"
              value={formData.route || ''}
              onChange={(value) => handleInputChange('route', value)}
              data={[
                { value: 'intramuscular', label: 'Intramuscular (IM)' },
                { value: 'subcutaneous', label: 'Subcutaneous (SC)' },
                { value: 'intradermal', label: 'Intradermal (ID)' },
                { value: 'oral', label: 'Oral' },
                { value: 'nasal', label: 'Nasal' },
                { value: 'intravenous', label: 'Intravenous (IV)' },
              ]}
              placeholder="Select administration route"
              clearable
              searchable
            />
          </Group>

          <DateInput
            label="Expiration Date"
            name="expiration_date"
            value={formData.expiration_date ? new Date(formData.expiration_date) : null}
            onChange={handleDateChange('expiration_date')}
            placeholder="Select expiration date"
          />

          <Select
            label="Practitioner"
            name="practitioner_id"
            value={formData.practitioner_id ? formData.practitioner_id.toString() : ''}
            onChange={(value) => handleInputChange('practitioner_id', value)}
            data={practitionerOptions}
            placeholder="Select administering practitioner"
            clearable
            searchable
          />

          <Textarea
            label="Notes"
            name="notes"
            value={formData.notes || ''}
            onChange={(e) => onInputChange(e)}
            placeholder="Enter any additional notes"
            rows={3}
          />

          {/* Form Actions */}
          <Group justify="flex-end" gap="sm">
            <Button variant="default" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <SubmitButton
              loading={isLoading}
              disabled={!formData.vaccine_name?.trim()}
            >
              {editingImmunization ? 'Update' : 'Create'} Immunization
            </SubmitButton>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
};

export default ImmunizationFormWrapper;