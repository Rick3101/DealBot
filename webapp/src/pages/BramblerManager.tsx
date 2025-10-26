import React from 'react';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { BramblerManagerContainer } from '@/containers/BramblerManagerContainer';
import { BramblerManagerPresenter } from '@/components/brambler/BramblerManagerPresenter';

/**
 * BramblerManager Page
 *
 * Manages secure pirate name anonymization using the Container/Presenter pattern.
 *
 * Architecture:
 * - BramblerManagerContainer: Manages state and business logic using custom hooks
 * - BramblerManagerPresenter: Pure presentational component for rendering UI
 *
 * Custom Hooks Used (via Container):
 * - useBramblerData: Data loading and management
 * - useBramblerDecryption: Decryption and master key operations
 * - useBramblerModals: Modal state management
 * - useBramblerActions: CRUD operations
 */
export const BramblerManager: React.FC = () => {
  return (
    <CaptainLayout
      title="Brambler - Name Manager"
      subtitle="Secure pirate name anonymization"
    >
      <BramblerManagerContainer>
        {(props) => <BramblerManagerPresenter {...props} />}
      </BramblerManagerContainer>
    </CaptainLayout>
  );
};
