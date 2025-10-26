import React from 'react';
import styled, { css } from 'styled-components';
import { motion } from 'framer-motion';
import { pirateColors, pirateTypography, spacing, mixins, media } from '@/utils/pirateTheme';
import { formatUserDisplay, isAvailable as isTelegramAvailable } from '@/utils/telegram';
import { websocketService } from '@/services/websocketService';

interface CaptainLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showUserInfo?: boolean;
  className?: string;
}

const LayoutContainer = styled.div`
  min-height: 100vh;
  min-height: 100dvh;
  background: linear-gradient(
    135deg,
    ${pirateColors.parchment} 0%,
    ${pirateColors.lightGold} 50%,
    ${pirateColors.parchment} 100%
  );
  color: ${pirateColors.primary};
  font-family: ${pirateTypography.body};
`;

const Header = styled.header`
  background: linear-gradient(145deg, ${pirateColors.primary}, ${pirateColors.darkBrown});
  color: ${pirateColors.white};
  padding: ${spacing.lg} ${spacing.lg} ${spacing.xl};
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23DAA520' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    pointer-events: none;
    opacity: 0.3;
  }

  ${media.sm(css`
    padding: ${spacing.xl} ${spacing.xl} ${spacing['2xl']};
  `)}
`;

const HeaderContent = styled.div`
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
`;

const HeaderTop = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: ${spacing.lg};

  ${media.sm(css`
    align-items: center;
  `)}
`;

const HeaderTitle = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
`;

const HeaderIcon = styled.span`
  font-size: 2.5rem;
  ${mixins.swayingShip}

  ${media.sm(css`
    font-size: 3rem;
  `)}
`;

const HeaderTextGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
`;

const Title = styled.h1`
  font-family: ${pirateTypography.headings};
  font-size: 1.75rem;
  font-weight: ${pirateTypography.weights.bold};
  margin: 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);

  ${media.sm(css`
    font-size: 2.5rem;
  `)}
`;

const Subtitle = styled.p`
  font-size: ${pirateTypography.sizes.base};
  margin: 0;
  opacity: 0.9;
  font-style: italic;

  ${media.sm(css`
    font-size: ${pirateTypography.sizes.lg};
  `)}
`;

const UserInfo = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: ${spacing.xs};
  background: rgba(255, 255, 255, 0.1);
  padding: ${spacing.sm} ${spacing.md};
  border-radius: 8px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);

  ${media.sm(css`
    flex-direction: row;
    align-items: center;
    gap: ${spacing.md};
  `)}
`;

const UserName = styled.span`
  font-weight: ${pirateTypography.weights.medium};
  font-size: ${pirateTypography.sizes.sm};

  ${media.sm(css`
    font-size: ${pirateTypography.sizes.base};
  `)}
`;

const UserRole = styled.span`
  font-size: ${pirateTypography.sizes.xs};
  opacity: 0.8;
  background: ${pirateColors.secondary};
  color: ${pirateColors.primary};
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 12px;
  font-weight: ${pirateTypography.weights.medium};

  ${media.sm(css`
    font-size: ${pirateTypography.sizes.sm};
  `)}
`;

const MainContent = styled.main`
  ${mixins.mobileFirst}
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: ${spacing['3xl']};
`;

const ConnectionStatus = styled(motion.div)<{ $connected: boolean }>`
  position: fixed;
  bottom: ${spacing.lg};
  right: ${spacing.lg};
  background: ${props => props.$connected ? pirateColors.success : pirateColors.danger};
  color: ${pirateColors.white};
  padding: ${spacing.sm} ${spacing.md};
  border-radius: 20px;
  font-size: ${pirateTypography.sizes.sm};
  font-weight: ${pirateTypography.weights.medium};
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;

  ${media.sm(css`
    bottom: ${spacing.xl};
    right: ${spacing.xl};
  `)}
`;

const StatusIndicator = styled.div<{ $connected: boolean }>`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: ${props => props.$connected ? pirateColors.white : pirateColors.lightGold};
  animation: ${props => props.$connected ? 'none' : 'pulse 1s infinite'};

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

export const CaptainLayout: React.FC<CaptainLayoutProps> = ({
  children,
  title = 'Captain\'s Expeditions',
  subtitle = 'Manage your pirate adventures',
  showUserInfo = true,
  className,
}) => {
  const [isWebSocketConnected, setIsWebSocketConnected] = React.useState(false);

  // Monitor real WebSocket connection status
  React.useEffect(() => {
    const checkConnection = () => {
      setIsWebSocketConnected(websocketService.isConnected());
    };

    // Check connection status on mount
    checkConnection();

    // Subscribe to connection events
    const handleConnected = () => setIsWebSocketConnected(true);
    const handleDisconnected = () => setIsWebSocketConnected(false);

    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);

    // Poll connection status every 5 seconds as backup
    const interval = setInterval(checkConnection, 5000);

    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      clearInterval(interval);
    };
  }, []);

  const userDisplay = isTelegramAvailable() ? formatUserDisplay() : 'Captain';
  const userRole = 'Expedition Leader';

  return (
    <LayoutContainer className={className}>
      <Header>
        <HeaderContent>
          <HeaderTop>
            <HeaderTitle
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <HeaderIcon>⛵</HeaderIcon>
              <HeaderTextGroup>
                <Title>{title}</Title>
                {subtitle && <Subtitle>{subtitle}</Subtitle>}
              </HeaderTextGroup>
            </HeaderTitle>

            {showUserInfo && (
              <UserInfo
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <UserName>{userDisplay}</UserName>
                <UserRole>{userRole}</UserRole>
              </UserInfo>
            )}
          </HeaderTop>
        </HeaderContent>
      </Header>

      <MainContent>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          {children}
        </motion.div>
      </MainContent>

      <ConnectionStatus
        $connected={isWebSocketConnected}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <StatusIndicator $connected={isWebSocketConnected} />
        {isWebSocketConnected ? 'Live Updates' : 'Connecting...'}
      </ConnectionStatus>
    </LayoutContainer>
  );
};