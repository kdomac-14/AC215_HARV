require('dotenv/config');

const appJson = require('./app.json');

module.exports = ({ config }) => {
  const baseExpoConfig = { ...(config?.expo ?? {}), ...(appJson.expo ?? {}) };

  return {
    ...appJson,
    expo: {
      ...baseExpoConfig,
      extra: {
        ...(baseExpoConfig.extra ?? {}),
        apiUrl: process.env.API_URL ?? 'http://localhost:8000',
      },
    },
  };
};
