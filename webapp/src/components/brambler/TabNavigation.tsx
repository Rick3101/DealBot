import React from 'react';
import styled, { css } from 'styled-components';
import { Users, Package } from 'lucide-react';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';

type TabKey = 'pirates' | 'items';

interface Tab {
  key: TabKey;
  label: string;
  icon: React.ReactNode;
  count?: number;
}

interface TabNavigationProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  piratesCount?: number;
  itemsCount?: number;
}

const TabContainer = styled.div`
  display: flex;
  gap: ${spacing.md};
  margin-bottom: ${spacing['2xl']};
  border-bottom: 2px solid ${pirateColors.lightGold};
  padding: 0 ${spacing.sm};

  @media (min-width: 640px) {
    padding: 0;
  }
`;

const TabButton = styled.button.attrs({ type: 'button' })<{ $active: boolean }>`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.sm};
  padding: ${spacing.md} ${spacing.lg};
  border: none;
  background: transparent;
  color: ${props => props.$active ? pirateColors.primary : pirateColors.muted};
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.base};
  font-weight: ${pirateTypography.weights.bold};
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;

  ${props => props.$active && css`
    color: ${pirateColors.primary};
    border-bottom-color: ${pirateColors.secondary};
  `}

  &:hover:not([disabled]) {
    color: ${pirateColors.primary};
    background: ${pirateColors.lightGold}30;
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  @media (min-width: 640px) {
    flex: initial;
    min-width: 180px;
  }
`;

const TabIcon = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
`;

const TabLabel = styled.span`
  display: none;

  @media (min-width: 480px) {
    display: inline;
  }
`;

const TabCount = styled.span<{ $active: boolean }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 ${spacing.xs};
  border-radius: 12px;
  background: ${props => props.$active ? pirateColors.secondary : pirateColors.muted};
  color: ${pirateColors.white};
  font-size: ${pirateTypography.sizes.xs};
  font-weight: ${pirateTypography.weights.bold};
  margin-left: ${spacing.xs};
`;

export const TabNavigation: React.FC<TabNavigationProps> = ({
  activeTab,
  onTabChange,
  piratesCount,
  itemsCount
}) => {
  const tabs: Tab[] = [
    {
      key: 'pirates',
      label: 'Pirates',
      icon: <Users size={20} />,
      count: piratesCount
    },
    {
      key: 'items',
      label: 'Items',
      icon: <Package size={20} />,
      count: itemsCount
    }
  ];

  const handleTabClick = (tabKey: TabKey) => {
    if (tabKey !== activeTab) {
      hapticFeedback('light');
      onTabChange(tabKey);
    }
  };

  return (
    <TabContainer>
      {tabs.map(tab => (
        <TabButton
          key={tab.key}
          $active={activeTab === tab.key}
          onClick={() => handleTabClick(tab.key)}
        >
          <TabIcon>{tab.icon}</TabIcon>
          <TabLabel>{tab.label}</TabLabel>
          {tab.count !== undefined && tab.count > 0 && (
            <TabCount $active={activeTab === tab.key}>
              {tab.count}
            </TabCount>
          )}
        </TabButton>
      ))}
    </TabContainer>
  );
};
