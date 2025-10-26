import React, { useState, useEffect } from 'react';
import styled, { css } from 'styled-components';
import { motion } from 'framer-motion';
import { formatDistance, isAfter, parseISO } from 'date-fns';
import { pirateColors, pirateTypography, spacing, mixins } from '@/utils/pirateTheme';

interface DeadlineTimerProps {
  deadline: string;
  showIcon?: boolean;
  compact?: boolean;
  className?: string;
}

interface TimeLeft {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isOverdue: boolean;
}

const TimerContainer = styled(motion.div)<{ $isOverdue: boolean; $compact: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: ${spacing.sm};
  padding: ${props => props.$compact ? spacing.sm : spacing.md};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-weight: ${pirateTypography.weights.medium};
  transition: all 0.3s ease;

  ${props => props.$isOverdue ? css`
    background: linear-gradient(135deg, ${pirateColors.danger}, #B91C1C);
    color: ${pirateColors.white};
    ${mixins.treasureGlow}
  ` : css`
    background: linear-gradient(135deg, ${pirateColors.lightGold}, ${pirateColors.parchment});
    color: ${pirateColors.primary};
    border: 1px solid ${pirateColors.secondary};
  `}

  ${props => props.$compact && css`
    font-size: ${pirateTypography.sizes.sm};
  `}
`;

const TimerIcon = styled.span<{ $isOverdue: boolean }>`
  font-size: 1.2em;
  animation: ${props => props.$isOverdue ? 'pulse 1s infinite' : 'none'};

  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }
`;

const TimeDisplay = styled.div<{ $compact: boolean }>`
  display: flex;
  align-items: center;
  gap: ${spacing.xs};

  ${props => props.$compact && css`
    flex-direction: column;
    gap: 0;
    line-height: 1.2;
  `}
`;

const TimeUnit = styled.span<{ $highlight?: boolean }>`
  font-weight: ${pirateTypography.weights.bold};

  ${props => props.$highlight && css`
    color: ${pirateColors.secondary};
    text-shadow: 0 0 4px rgba(218, 165, 32, 0.5);
  `}
`;

const TimeLabel = styled.span`
  font-size: 0.85em;
  opacity: 0.8;
`;

export const DeadlineTimer: React.FC<DeadlineTimerProps> = ({
  deadline,
  showIcon = true,
  compact = false,
  className,
}) => {
  const [timeLeft, setTimeLeft] = useState<TimeLeft>({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    isOverdue: false,
  });

  const calculateTimeLeft = (): TimeLeft => {
    const now = new Date();
    const deadlineDate = parseISO(deadline);
    const isOverdue = isAfter(now, deadlineDate);

    if (isOverdue) {
      return {
        days: 0,
        hours: 0,
        minutes: 0,
        seconds: 0,
        isOverdue: true,
      };
    }

    const timeDiff = deadlineDate.getTime() - now.getTime();

    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

    return {
      days,
      hours,
      minutes,
      seconds,
      isOverdue: false,
    };
  };

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(calculateTimeLeft());
    }, 1000);

    // Calculate initial time
    setTimeLeft(calculateTimeLeft());

    return () => clearInterval(timer);
  }, [deadline]);

  const formatTimeLeft = (): string => {
    if (timeLeft.isOverdue) {
      const deadlineDate = parseISO(deadline);
      return `Overdue by ${formatDistance(deadlineDate, new Date())}`;
    }

    if (timeLeft.days > 0) {
      return `${timeLeft.days}d ${timeLeft.hours}h ${timeLeft.minutes}m`;
    }

    if (timeLeft.hours > 0) {
      return `${timeLeft.hours}h ${timeLeft.minutes}m ${timeLeft.seconds}s`;
    }

    if (timeLeft.minutes > 0) {
      return `${timeLeft.minutes}m ${timeLeft.seconds}s`;
    }

    return `${timeLeft.seconds}s`;
  };

  const getTimerIcon = (): string => {
    if (timeLeft.isOverdue) return '💀';
    if (timeLeft.days === 0 && timeLeft.hours < 2) return '⚠️';
    if (timeLeft.days === 0) return '⏰';
    return '🧭';
  };

  const renderDetailedTime = () => {
    if (timeLeft.isOverdue) {
      return (
        <TimeDisplay $compact={compact}>
          <TimeUnit $highlight>OVERDUE</TimeUnit>
        </TimeDisplay>
      );
    }

    if (compact) {
      return (
        <TimeDisplay $compact>
          <TimeUnit>{formatTimeLeft()}</TimeUnit>
        </TimeDisplay>
      );
    }

    const showSeconds = timeLeft.days === 0 && timeLeft.hours < 1;

    return (
      <TimeDisplay $compact={false}>
        {timeLeft.days > 0 && (
          <>
            <TimeUnit $highlight={timeLeft.days <= 1}>{timeLeft.days}</TimeUnit>
            <TimeLabel>d</TimeLabel>
          </>
        )}
        {(timeLeft.days > 0 || timeLeft.hours > 0) && (
          <>
            <TimeUnit $highlight={timeLeft.days === 0 && timeLeft.hours < 3}>{timeLeft.hours}</TimeUnit>
            <TimeLabel>h</TimeLabel>
          </>
        )}
        {timeLeft.days === 0 && (
          <>
            <TimeUnit $highlight={timeLeft.hours === 0 && timeLeft.minutes < 10}>{timeLeft.minutes}</TimeUnit>
            <TimeLabel>m</TimeLabel>
          </>
        )}
        {showSeconds && (
          <>
            <TimeUnit $highlight>{timeLeft.seconds}</TimeUnit>
            <TimeLabel>s</TimeLabel>
          </>
        )}
      </TimeDisplay>
    );
  };

  return (
    <TimerContainer
      className={className}
      $isOverdue={timeLeft.isOverdue}
      $compact={compact}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {showIcon && (
        <TimerIcon $isOverdue={timeLeft.isOverdue}>
          {getTimerIcon()}
        </TimerIcon>
      )}
      {renderDetailedTime()}
    </TimerContainer>
  );
};