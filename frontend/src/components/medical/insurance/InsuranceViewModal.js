import React from 'react';
import {
  Modal,
  Title,
  Text,
  Grid,
  Group,
  Badge,
  Button,
  Stack,
  Divider,
  ActionIcon,
  Card,
} from '@mantine/core';
import { IconEdit, IconPrinter, IconStar } from '@tabler/icons-react';
import { formatDate } from '../../../utils/helpers';
import { formatPhoneNumber, cleanPhoneNumber, isPhoneField } from '../../../utils/phoneUtils';
import { formatFieldLabel, formatFieldValue } from '../../../utils/fieldFormatters';
import StatusBadge from '../StatusBadge';
import DocumentSection from '../../shared/DocumentSection';

const InsuranceViewModal = ({ 
  isOpen, 
  onClose, 
  insurance, 
  onEdit, 
  onPrint, 
  onSetPrimary,
  onFileUploadComplete
}) => {
  if (!insurance) return null;

  // Get type-specific styling
  const getTypeColor = (type) => {
    switch (type) {
      case 'medical': return 'blue';
      case 'dental': return 'green';
      case 'vision': return 'purple';
      case 'prescription': return 'orange';
      default: return 'gray';
    }
  };

  // Using imported formatters from utilities

  const typeColor = getTypeColor(insurance.insurance_type);

  // Get relevant coverage and contact fields to display
  const coverageDetails = insurance.coverage_details || {};
  const contactInfo = insurance.contact_info || {};

  return (
    <Modal
      opened={isOpen}
      onClose={onClose}
      title={
        <Group position="apart" style={{ width: '100%' }}>
          <Group>
            <Title order={3}>Insurance Details</Title>
            <StatusBadge status={insurance.status} />
          </Group>
        </Group>
      }
      size="lg"
      centered
      styles={{
        body: { padding: '1.5rem' },
        header: { paddingBottom: '1rem' },
      }}
    >
      <Stack spacing="lg">
        {/* Header Section */}
        <Card withBorder p="md" style={{ backgroundColor: '#f8f9fa' }}>
          <Group position="apart" align="flex-start">
            <Stack spacing={8}>
              <Group>
                <Title order={2} color={typeColor}>
                  {insurance.company_name}
                </Title>
                <Badge 
                  size="lg" 
                  variant="light" 
                  color={typeColor}
                  style={{ textTransform: 'capitalize' }}
                >
                  {insurance.insurance_type} Insurance
                </Badge>
                {insurance.insurance_type === 'medical' && insurance.is_primary && (
                  <Badge size="sm" variant="filled" color="yellow" leftSection={<IconStar size={12} />}>
                    Primary
                  </Badge>
                )}
              </Group>
              {insurance.plan_name && (
                <Text size="sm" color="dimmed">
                  Plan: {insurance.plan_name}
                </Text>
              )}
              {insurance.employer_group && (
                <Text size="sm" color="dimmed">
                  Group: {insurance.employer_group}
                </Text>
              )}
            </Stack>
          </Group>
        </Card>

        {/* Basic Information */}
        <div>
          <Title order={4} mb="sm">Member Information</Title>
          <Grid>
            <Grid.Col span={6}>
              <Text size="sm" weight={500} color="dimmed">Member Name</Text>
              <Text>{insurance.member_name}</Text>
            </Grid.Col>
            {insurance.policy_holder_name && insurance.policy_holder_name !== insurance.member_name ? (
              <Grid.Col span={6}>
                <Text size="sm" weight={500} color="dimmed">Policy Holder</Text>
                <Text>{insurance.policy_holder_name}</Text>
              </Grid.Col>
            ) : (
              <Grid.Col span={6}>
                <Text size="sm" weight={500} color="dimmed">Policy Holder</Text>
                <Text color="dimmed">Same as member</Text>
              </Grid.Col>
            )}
            <Grid.Col span={6}>
              <Text size="sm" weight={500} color="dimmed">Member ID</Text>
              <Text>{insurance.member_id}</Text>
            </Grid.Col>
            {insurance.policy_holder_name && insurance.policy_holder_name !== insurance.member_name && (
              <Grid.Col span={6}>
                <Text size="sm" weight={500} color="dimmed">Relationship</Text>
                <Text style={{ textTransform: 'capitalize' }}>
                  {insurance.relationship_to_holder || 'Self'}
                </Text>
              </Grid.Col>
            )}
            {insurance.group_number && (
              <Grid.Col span={6}>
                <Text size="sm" weight={500} color="dimmed">Group Number</Text>
                <Text>{insurance.group_number}</Text>
              </Grid.Col>
            )}
            {insurance.employer_group && (
              <Grid.Col span={6}>
                <Text size="sm" weight={500} color="dimmed">Employer/Group Sponsor</Text>
                <Text>{insurance.employer_group}</Text>
              </Grid.Col>
            )}
          </Grid>
        </div>

        {/* Coverage Period */}
        <div>
          <Title order={4} mb="sm">Coverage Period</Title>
          <Grid>
            <Grid.Col span={6}>
              <Text size="sm" weight={500} color="dimmed">Effective Date</Text>
              <Text>{formatDate(insurance.effective_date)}</Text>
            </Grid.Col>
            <Grid.Col span={6}>
              <Text size="sm" weight={500} color="dimmed">Expiration Date</Text>
              <Text>
                {insurance.expiration_date ? formatDate(insurance.expiration_date) : 'Ongoing'}
              </Text>
            </Grid.Col>
          </Grid>
        </div>

        {/* Coverage Details */}
        {Object.keys(coverageDetails).length > 0 && (
          <div>
            <Title order={4} mb="sm">Coverage Details</Title>
            <Grid>
              {Object.entries(coverageDetails).map(([key, value]) => (
                <Grid.Col span={6} key={key}>
                  <Text size="sm" weight={500} color="dimmed">
                    {formatFieldLabel(key)}
                  </Text>
                  <Text>{formatFieldValue(key, value)}</Text>
                </Grid.Col>
              ))}
            </Grid>
          </div>
        )}

        {/* Contact Information */}
        {Object.keys(contactInfo).length > 0 && (
          <div>
            <Title order={4} mb="sm">Contact Information</Title>
            <Grid>
              {Object.entries(contactInfo).map(([key, value]) => (
                <Grid.Col span={key === 'claims_address' || key === 'pharmacy_network_info' ? 12 : 6} key={key}>
                  <Text size="sm" weight={500} color="dimmed">
                    {formatFieldLabel(key)}
                  </Text>
                  <Text style={key === 'website_url' ? { wordBreak: 'break-all' } : {}}>
                    {isPhoneField(key) ? formatPhoneNumber(cleanPhoneNumber(value)) : value}
                  </Text>
                </Grid.Col>
              ))}
            </Grid>
          </div>
        )}

        {/* Notes */}
        {insurance.notes && (
          <div>
            <Title order={4} mb="sm">Notes</Title>
            <Text style={{ whiteSpace: 'pre-wrap' }}>{insurance.notes}</Text>
          </div>
        )}

        {/* Document Management */}
        <DocumentSection
          entityType="insurance"
          entityId={insurance.id}
          mode="view"
          onUploadComplete={(success, completedCount, failedCount) => {
            if (onFileUploadComplete) {
              onFileUploadComplete(success);
            }
          }}
          onError={(error) => {
            console.error('Document manager error in insurance view:', error);
          }}
        />

        {/* Action Buttons */}
        <Divider />
        <Group position="apart">
          <Group>
            <Button
              variant="outline"
              leftSection={<IconPrinter size={16} />}
              onClick={() => onPrint && onPrint(insurance)}
            >
              Print Card
            </Button>
          </Group>
          <Group>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            <Button
              leftSection={<IconEdit size={16} />}
              onClick={() => {
                onClose();
                onEdit && onEdit(insurance);
              }}
            >
              Edit
            </Button>
          </Group>
        </Group>
      </Stack>
    </Modal>
  );
};

export default InsuranceViewModal;