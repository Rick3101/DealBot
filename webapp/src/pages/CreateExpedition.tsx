import React from 'react';
import { CreateExpeditionContainer } from '@/containers/CreateExpeditionContainer';

/**
 * CreateExpedition page component
 * Thin wrapper that delegates to CreateExpeditionContainer
 */
export const CreateExpedition: React.FC = () => {
  return <CreateExpeditionContainer />;
};
