interface Config {
  apiUrl: string;
  environment: 'development' | 'production';
  sentryDsn?: string;
  version: string;
}

const config: Config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8765',
  environment: (process.env.NODE_ENV as 'development' | 'production') || 'development',
  sentryDsn: process.env.REACT_APP_SENTRY_DSN,
  version: process.env.REACT_APP_VERSION || '1.0.0',
};

export { config }; 