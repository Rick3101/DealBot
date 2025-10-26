import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';

export interface WarningBannerProps {
  /**
   * Type of banner determining color scheme and icon
   */
  type?: 'warning' | 'error' | 'info' | 'success';

  /**
   * Optional title for the banner
   */
  title?: string;

  /**
   * Message to display
   */
  message: string;

  /**
   * Custom icon to override default type icon
   */
  icon?: React.ReactNode;

  /**
   * Additional CSS styles
   */
  style?: React.CSSProperties;
}

const typeConfig = {
  warning: {
    icon: AlertTriangle,
    gradient: `linear-gradient(135deg, ${pirateColors.warning}20, ${pirateColors.danger}10)`,
    borderColor: pirateColors.warning,
    iconColor: pirateColors.warning,
  },
  error: {
    icon: XCircle,
    gradient: `linear-gradient(135deg, ${pirateColors.danger}20, ${pirateColors.danger}15)`,
    borderColor: pirateColors.danger,
    iconColor: pirateColors.danger,
  },
  info: {
    icon: Info,
    gradient: `linear-gradient(135deg, ${pirateColors.secondary}20, ${pirateColors.secondary}10)`,
    borderColor: pirateColors.secondary,
    iconColor: pirateColors.secondary,
  },
  success: {
    icon: CheckCircle,
    gradient: `linear-gradient(135deg, ${pirateColors.success}20, ${pirateColors.success}10)`,
    borderColor: pirateColors.success,
    iconColor: pirateColors.success,
  },
};

const BannerContainer = styled(motion.div)<{ $type: keyof typeof typeConfig }>`
  background: ${props => typeConfig[props.$type].gradient};
  border: 2px solid ${props => typeConfig[props.$type].borderColor};
  border-radius: 12px;
  padding: ${spacing.md};
  margin-bottom: ${spacing.md};
  display: flex;
  align-items: flex-start;
  gap: ${spacing.md};
`;

const IconContainer = styled.div<{ $type: keyof typeof typeConfig }>`
  flex-shrink: 0;
  color: ${props => typeConfig[props.$type].iconColor};
  margin-top: 2px;
`;

const ContentContainer = styled.div`
  flex: 1;
  min-width: 0;
`;

const BannerTitle = styled.h4`
  color: ${pirateColors.primary};
  font-weight: ${pirateTypography.weights.bold};
  font-size: ${pirateTypography.sizes.base};
  margin: 0 0 ${spacing.xs} 0;
  font-family: ${pirateTypography.headings};
`;

const BannerMessage = styled.p`
  color: ${pirateColors.muted};
  margin: 0;
  font-size: ${pirateTypography.sizes.sm};
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
`;

/**
 * WarningBanner Component
 *
 * Displays contextual banners for warnings, errors, info, and success messages.
 * Supports custom icons, titles, and automatic color theming based on type.
 *
 * @example
 * ```tsx
 * <WarningBanner
 *   type="warning"
 *   title="Security Warning"
 *   message="Real names are currently visible. Switch back to pirate names when finished."
 * />
 *
 * <WarningBanner
 *   type="error"
 *   message="Failed to load data. Please try again."
 * />
 *
 * <WarningBanner
 *   type="success"
 *   message="Pirate created successfully!"
 * />
 * ```
 */
export const WarningBanner: React.FC<WarningBannerProps> = ({
  type = 'warning',
  title,
  message,
  icon,
  style,
}) => {
  const config = typeConfig[type];
  const DefaultIcon = config.icon;

  return (
    <BannerContainer
      $type={type}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      style={style}
    >
      <IconContainer $type={type}>
        {icon || <DefaultIcon size={20} />}
      </IconContainer>
      <ContentContainer>
        {title && <BannerTitle>{title}</BannerTitle>}
        <BannerMessage>{message}</BannerMessage>
      </ContentContainer>
    </BannerContainer>
  );
};
