import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { PirateCard } from '@/components/ui/PirateCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { logger, LogLevel, LogEntry } from '@/services/loggerService';
import { Download, Trash2, RefreshCw } from 'lucide-react';

const PageContainer = styled.div`
  padding: ${spacing.lg};
  max-width: 1400px;
  margin: 0 auto;
`;

const PageHeader = styled.div`
  margin-bottom: ${spacing.xl};
`;

const PageTitle = styled.h1`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes['3xl']};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${spacing.md};
  margin-bottom: ${spacing.xl};
`;

const StatCard = styled(PirateCard)`
  text-align: center;
  padding: ${spacing.lg};
`;

const StatValue = styled.div`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes['2xl']};
  color: ${pirateColors.secondary};
  margin-bottom: ${spacing.xs};
`;

const StatLabel = styled.div`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
`;

const ControlsContainer = styled.div`
  display: flex;
  gap: ${spacing.md};
  flex-wrap: wrap;
  margin-bottom: ${spacing.lg};
  align-items: center;
`;

const FilterGroup = styled.div`
  display: flex;
  gap: ${spacing.sm};
  align-items: center;
`;

const FilterLabel = styled.span`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  margin-right: ${spacing.xs};
`;

const Select = styled.select`
  padding: ${spacing.sm} ${spacing.md};
  border: 2px solid ${pirateColors.primary};
  border-radius: 8px;
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.sm};
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
  }
`;

const LogsContainer = styled.div`
  background: ${pirateColors.white};
  border: 2px solid ${pirateColors.primary};
  border-radius: 12px;
  overflow: hidden;
`;

const LogsTable = styled.div`
  max-height: 600px;
  overflow-y: auto;
`;

const LogRow = styled(motion.div)<{ $level: LogLevel }>`
  padding: ${spacing.md};
  border-bottom: 1px solid ${pirateColors.lightGold};
  display: grid;
  grid-template-columns: auto 80px 120px 1fr;
  gap: ${spacing.md};
  align-items: start;
  font-size: ${pirateTypography.sizes.sm};

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: ${pirateColors.lightGold};
  }

  ${(props) => {
    switch (props.$level) {
      case LogLevel.ERROR:
      case LogLevel.FATAL:
        return `background: rgba(220, 20, 60, 0.05);`;
      case LogLevel.WARN:
        return `background: rgba(255, 140, 0, 0.05);`;
      default:
        return '';
    }
  }}
`;

const LogTime = styled.div`
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.xs};
  white-space: nowrap;
`;

const LogLevel_Badge = styled.div<{ $level: LogLevel }>`
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 4px;
  font-weight: ${pirateTypography.weights.bold};
  font-size: ${pirateTypography.sizes.xs};
  text-align: center;
  text-transform: uppercase;

  ${(props) => {
    switch (props.$level) {
      case LogLevel.DEBUG:
        return `background: ${pirateColors.info}; color: white;`;
      case LogLevel.INFO:
        return `background: ${pirateColors.success}; color: white;`;
      case LogLevel.WARN:
        return `background: ${pirateColors.warning}; color: white;`;
      case LogLevel.ERROR:
        return `background: ${pirateColors.danger}; color: white;`;
      case LogLevel.FATAL:
        return `background: ${pirateColors.black}; color: white;`;
      default:
        return `background: ${pirateColors.muted}; color: white;`;
    }
  }}
`;

const LogContext = styled.div`
  color: ${pirateColors.primary};
  font-weight: ${pirateTypography.weights.medium};
  font-family: ${pirateTypography.headings};
`;

const LogMessage = styled.div`
  color: ${pirateColors.primary};
  word-break: break-word;
`;

const LogDetails = styled.div`
  grid-column: 1 / -1;
  margin-top: ${spacing.sm};
  padding: ${spacing.sm};
  background: rgba(139, 69, 19, 0.05);
  border-radius: 4px;
  font-family: monospace;
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  max-height: 200px;
  overflow-y: auto;
`;

const EmptyState = styled.div`
  padding: ${spacing['3xl']};
  text-align: center;
  color: ${pirateColors.muted};
`;

const EmptyIcon = styled.div`
  font-size: 4rem;
  margin-bottom: ${spacing.md};
`;

export const LogViewer: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [levelFilter, setLevelFilter] = useState<LogLevel | 'all'>('all');
  const [contextFilter, setContextFilter] = useState<string>('all');
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  const [contexts, setContexts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const options: any = { limit: 500 };
      if (levelFilter !== 'all') options.level = levelFilter;
      if (contextFilter !== 'all') options.context = contextFilter;

      const fetchedLogs = await logger.getLogs(options);
      setLogs(fetchedLogs);

      // Extract unique contexts
      const uniqueContexts = Array.from(new Set(fetchedLogs.map((log) => log.context).filter(Boolean))) as string[];
      setContexts(uniqueContexts);
    } catch (error) {
      console.error('Failed to load logs', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const fetchedStats = await logger.getStats();
      setStats(fetchedStats);
    } catch (error) {
      console.error('Failed to load stats', error);
    }
  };

  useEffect(() => {
    loadLogs();
    loadStats();
  }, [levelFilter, contextFilter]);

  const handleClearLogs = async () => {
    if (window.confirm('Are you sure you want to clear all logs? This cannot be undone.')) {
      await logger.clearLogs();
      await loadLogs();
      await loadStats();
    }
  };

  const handleDownloadJSON = async () => {
    await logger.downloadLogs('json');
  };

  const handleDownloadCSV = async () => {
    await logger.downloadLogs('csv');
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <CaptainLayout>
      <PageContainer>
        <PageHeader>
          <PageTitle>📜 Log Viewer</PageTitle>
        </PageHeader>

        {stats && (
          <StatsContainer>
            <StatCard>
              <StatValue>{stats.total}</StatValue>
              <StatLabel>Total Logs</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{stats.byLevel[LogLevel.ERROR] + stats.byLevel[LogLevel.FATAL]}</StatValue>
              <StatLabel>Errors</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{stats.byLevel[LogLevel.WARN]}</StatValue>
              <StatLabel>Warnings</StatLabel>
            </StatCard>
            <StatCard>
              <StatValue>{stats.byLevel[LogLevel.INFO]}</StatValue>
              <StatLabel>Info</StatLabel>
            </StatCard>
          </StatsContainer>
        )}

        <ControlsContainer>
          <FilterGroup>
            <FilterLabel>Level:</FilterLabel>
            <Select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value as any)}>
              <option value="all">All Levels</option>
              <option value={LogLevel.DEBUG}>Debug</option>
              <option value={LogLevel.INFO}>Info</option>
              <option value={LogLevel.WARN}>Warning</option>
              <option value={LogLevel.ERROR}>Error</option>
              <option value={LogLevel.FATAL}>Fatal</option>
            </Select>
          </FilterGroup>

          <FilterGroup>
            <FilterLabel>Context:</FilterLabel>
            <Select value={contextFilter} onChange={(e) => setContextFilter(e.target.value)}>
              <option value="all">All Contexts</option>
              {contexts.map((ctx) => (
                <option key={ctx} value={ctx}>
                  {ctx}
                </option>
              ))}
            </Select>
          </FilterGroup>

          <PirateButton size="sm" onClick={loadLogs}>
            <RefreshCw size={16} /> Refresh
          </PirateButton>

          <PirateButton size="sm" variant="secondary" onClick={handleDownloadJSON}>
            <Download size={16} /> JSON
          </PirateButton>

          <PirateButton size="sm" variant="secondary" onClick={handleDownloadCSV}>
            <Download size={16} /> CSV
          </PirateButton>

          <PirateButton size="sm" variant="danger" onClick={handleClearLogs}>
            <Trash2 size={16} /> Clear All
          </PirateButton>
        </ControlsContainer>

        <LogsContainer>
          {loading ? (
            <EmptyState>
              <EmptyIcon>⏳</EmptyIcon>
              <div>Loading logs...</div>
            </EmptyState>
          ) : logs.length === 0 ? (
            <EmptyState>
              <EmptyIcon>📭</EmptyIcon>
              <div>No logs found</div>
            </EmptyState>
          ) : (
            <LogsTable>
              <AnimatePresence>
                {logs.map((log) => (
                  <LogRow
                    key={log.id}
                    $level={log.level}
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id!)}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <LogTime>{formatTimestamp(log.timestamp)}</LogTime>
                    <LogLevel_Badge $level={log.level}>{log.level}</LogLevel_Badge>
                    <LogContext>{log.context || '-'}</LogContext>
                    <LogMessage>{log.message}</LogMessage>

                    {expandedLog === log.id && (
                      <LogDetails>
                        <div>
                          <strong>URL:</strong> {log.url}
                        </div>
                        {log.data && (
                          <div>
                            <strong>Data:</strong> {JSON.stringify(log.data, null, 2)}
                          </div>
                        )}
                        {log.stackTrace && (
                          <div>
                            <strong>Stack Trace:</strong>
                            <pre>{log.stackTrace}</pre>
                          </div>
                        )}
                        <div>
                          <strong>User Agent:</strong> {log.userAgent}
                        </div>
                      </LogDetails>
                    )}
                  </LogRow>
                ))}
              </AnimatePresence>
            </LogsTable>
          )}
        </LogsContainer>
      </PageContainer>
    </CaptainLayout>
  );
};
