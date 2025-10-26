/**
 * AppRouter Component
 *
 * Centralized route configuration for the application.
 * Separates routing logic from App.tsx for better maintainability.
 */

import React from 'react';
import { Routes, Route, Navigate, useParams, useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Pages
import { Dashboard } from '@/pages/Dashboard';
import { CreateExpedition } from '@/pages/CreateExpedition';
import { ExpeditionDetails } from '@/pages/ExpeditionDetails';
import { BramblerManager } from '@/pages/BramblerManager';
import { BramblerMaintenance } from '@/pages/BramblerMaintenance';
import { LogViewer } from '@/pages/LogViewer';

/**
 * Wrapper component for ExpeditionDetails to handle URL parameters
 */
const ExpeditionDetailsWrapper: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/');
  };

  return (
    <ExpeditionDetails
      expeditionId={parseInt(id || '0')}
      onBack={handleBack}
    />
  );
};

/**
 * Route configuration type
 */
export interface RouteConfig {
  path: string;
  element: React.ReactElement;
  title?: string;
}

/**
 * Application routes configuration
 */
export const routes: RouteConfig[] = [
  {
    path: '/',
    element: <Dashboard />,
    title: 'Dashboard',
  },
  {
    path: '/dashboard',
    element: <Navigate to="/" replace />,
    title: 'Dashboard Redirect',
  },
  {
    path: '/expeditions',
    element: <Navigate to="/" replace />,
    title: 'Expeditions Redirect',
  },
  {
    path: '/expedition/create',
    element: <CreateExpedition />,
    title: 'Create Expedition',
  },
  {
    path: '/expedition/:id',
    element: <ExpeditionDetailsWrapper />,
    title: 'Expedition Details',
  },
  {
    path: '/brambler',
    element: <BramblerManager />,
    title: 'Brambler Manager',
  },
  {
    path: '/brambler/maintenance',
    element: <BramblerMaintenance />,
    title: 'Brambler Maintenance',
  },
  {
    path: '/logs',
    element: <LogViewer />,
    title: 'Log Viewer',
  },
];

/**
 * Main app router component
 */
export const AppRouter: React.FC = () => {
  return (
    <AnimatePresence mode="wait">
      <Routes>
        {routes.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            element={route.element}
          />
        ))}

        {/* Catch-all route - redirect to dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
};

/**
 * Navigation helper functions
 */
export const navigation = {
  dashboard: () => '/',
  createExpedition: () => '/expedition/create',
  expeditionDetails: (id: number | string) => `/expedition/${id}`,
  brambler: () => '/brambler',
  bramblerMaintenance: () => '/brambler/maintenance',
  logs: () => '/logs',
};
