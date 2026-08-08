export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;

  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'FinAssist',

  pageTitle: 'FinAssist — AI Financial Voice Assistant',

  pageDescription:
    'Your intelligent voice assistant for Banking, UPI, Loans, Credit Cards, Insurance and Digital Payments.',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/murf-logo.svg',
  logoDark: '/murf-logo-dark.svg',

  accent: '#10B981',
  accentDark: '#34D399',

  startButtonText: 'Start talking',

  // Audio visualizer
  audioVisualizerType: 'radial',
  audioVisualizerColor: '#10B981',
  audioVisualizerColorDark: '#34D399',
  audioVisualizerRadialBarCount: 24,
  audioVisualizerRadialRadius: 100,

  // Agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};