import { css } from 'styled-components';

// Pirate color palette
export const pirateColors = {
  primary: '#8B4513',      // Pirate brown
  secondary: '#DAA520',    // Gold
  danger: '#DC143C',       // Crimson
  success: '#228B22',      // Forest green
  water: '#4682B4',        // Steel blue
  parchment: '#F5DEB3',    // Wheat/parchment
  darkBrown: '#654321',    // Dark brown
  lightGold: '#F4E4BC',    // Light gold
  warning: '#FF8C00',      // Dark orange
  info: '#4682B4',         // Steel blue
  muted: '#A0522D',        // Sienna
  white: '#FFFEF7',        // Off-white
  black: '#2F1B0C',        // Dark brown-black
} as const;

// Typography
export const pirateTypography = {
  headings: "'Pirata One', cursive",
  body: "'Roboto', sans-serif",
  sizes: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
    '5xl': '3rem',      // 48px
  },
  weights: {
    light: 300,
    normal: 400,
    medium: 500,
    bold: 700,
  },
} as const;

// Spacing scale
export const spacing = {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.5rem',     // 24px
  '2xl': '2rem',    // 32px
  '3xl': '3rem',    // 48px
  '4xl': '4rem',    // 64px
  '5xl': '6rem',    // 96px
} as const;

// Breakpoints for responsive design
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
} as const;

// Animation keyframes
export const pirateAnimations = {
  sparkle: css`
    @keyframes sparkle {
      0%, 100% {
        transform: scale(1) rotate(0deg);
        opacity: 1;
      }
      50% {
        transform: scale(1.1) rotate(180deg);
        opacity: 0.8;
      }
    }
  `,
  sway: css`
    @keyframes sway {
      0%, 100% { transform: rotate(-2deg); }
      50% { transform: rotate(2deg); }
    }
  `,
  wave: css`
    @keyframes wave {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      75% { transform: translateX(5px); }
    }
  `,
  fadeIn: css`
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `,
  slideIn: css`
    @keyframes slideIn {
      from { transform: translateX(-100%); }
      to { transform: translateX(0); }
    }
  `,
  bounce: css`
    @keyframes bounce {
      0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
      40%, 43% { transform: translate3d(0, -10px, 0); }
      70% { transform: translate3d(0, -5px, 0); }
      90% { transform: translate3d(0, -2px, 0); }
    }
  `,
  pulse: css`
    @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
    }
  `,
  float: css`
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
    }
  `,
} as const;

// Pirate emojis and icons
export const pirateEmojis = {
  expedition: '⛵',
  treasure: '💰',
  skull: '💀',
  map: '🗺️',
  compass: '🧭',
  sword: '⚔️',
  anchor: '⚓',
  flag: '🏴‍☠️',
  gem: '💎',
  crown: '👑',
  items: {
    berry: '🫐',
    syrup: '🍯',
    salt: '🧂',
    candy: '🍬',
    rum: '🍺',
    bread: '🍞',
    meat: '🥩',
    fish: '🐟',
  },
  status: {
    active: '🟢',
    completed: '✅',
    cancelled: '❌',
    warning: '⚠️',
    overdue: '🔴',
  },
  quality: {
    A: '🌟',
    B: '⭐',
    C: '🔸',
  },
} as const;

// Common CSS mixins
export const mixins = {
  pirateCard: css`
    background: linear-gradient(135deg, ${pirateColors.parchment}, ${pirateColors.lightGold});
    border: 2px solid ${pirateColors.primary};
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(139, 69, 19, 0.25);
    }
  `,

  pirateButton: css`
    background: linear-gradient(145deg, ${pirateColors.secondary}, ${pirateColors.primary});
    border: none;
    border-radius: 8px;
    color: ${pirateColors.white};
    font-family: ${pirateTypography.headings};
    font-weight: ${pirateTypography.weights.bold};
    padding: ${spacing.md} ${spacing.xl};
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.2);

    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
    }

    &:active {
      transform: translateY(0);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  `,

  treasureGlow: css`
    animation: sparkle 2s infinite;
    filter: drop-shadow(0 0 8px ${pirateColors.secondary});
  `,

  swayingShip: css`
    animation: sway 3s ease-in-out infinite;
  `,

  wavingFlag: css`
    animation: wave 4s linear infinite;
  `,

  fadeInUp: css`
    animation: fadeIn 0.6s ease-out;
  `,

  responsiveText: css`
    font-size: ${pirateTypography.sizes.base};

    @media (max-width: ${breakpoints.sm}) {
      font-size: ${pirateTypography.sizes.sm};
    }
  `,

  mobileFirst: css`
    /* Mobile first approach */
    padding: ${spacing.md};

    @media (min-width: ${breakpoints.sm}) {
      padding: ${spacing.lg};
    }

    @media (min-width: ${breakpoints.md}) {
      padding: ${spacing.xl};
    }
  `,
} as const;

// Status color mapping
export const statusColors = {
  active: pirateColors.success,
  completed: pirateColors.info,
  cancelled: pirateColors.muted,
  overdue: pirateColors.danger,
  warning: pirateColors.warning,
  pending: pirateColors.warning,
  paid: pirateColors.success,
  partial: pirateColors.warning,
} as const;

// Quality grade colors
export const qualityColors = {
  A: pirateColors.secondary,  // Gold for premium
  B: pirateColors.info,       // Blue for standard
  C: pirateColors.muted,      // Brown for basic
} as const;

// Z-index layers
export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modal: 1040,
  popover: 1050,
  tooltip: 1060,
  loading: 9999,
} as const;

// Shadow presets
export const shadows = {
  sm: '0 1px 3px rgba(139, 69, 19, 0.1)',
  md: '0 4px 6px rgba(139, 69, 19, 0.1)',
  lg: '0 10px 15px rgba(139, 69, 19, 0.1)',
  xl: '0 20px 25px rgba(139, 69, 19, 0.1)',
  inner: 'inset 0 2px 4px rgba(139, 69, 19, 0.1)',
} as const;

// Utility functions
export const getStatusColor = (status: string): string => {
  return statusColors[status as keyof typeof statusColors] || pirateColors.muted;
};

export const getQualityColor = (quality: string): string => {
  return qualityColors[quality as keyof typeof qualityColors] || pirateColors.muted;
};

export const getStatusEmoji = (status: string): string => {
  return pirateEmojis.status[status as keyof typeof pirateEmojis.status] || '📦';
};

export const getQualityEmoji = (quality: string): string => {
  return pirateEmojis.quality[quality as keyof typeof pirateEmojis.quality] || '🔸';
};

// Responsive helper function
export const media = {
  sm: (styles: any) => css`
    @media (min-width: ${breakpoints.sm}) {
      ${styles}
    }
  `,
  md: (styles: any) => css`
    @media (min-width: ${breakpoints.md}) {
      ${styles}
    }
  `,
  lg: (styles: any) => css`
    @media (min-width: ${breakpoints.lg}) {
      ${styles}
    }
  `,
  xl: (styles: any) => css`
    @media (min-width: ${breakpoints.xl}) {
      ${styles}
    }
  `,
};