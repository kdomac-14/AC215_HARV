require('dotenv/config');

const appJson = require('./app.json');

module.exports = ({ config }) => {
  const baseExpoConfig = { ...(config?.expo ?? {}), ...(appJson.expo ?? {}) };
  const extra = { ...(baseExpoConfig.extra ?? {}) };
  const envApiUrl =
    (typeof process.env.EXPO_PUBLIC_API_URL === 'string' &&
      process.env.EXPO_PUBLIC_API_URL.trim().length > 0 &&
      process.env.EXPO_PUBLIC_API_URL.trim()) ||
    (typeof process.env.API_URL === 'string' &&
      process.env.API_URL.trim().length > 0 &&
      process.env.API_URL.trim()) ||
    undefined;

  if (envApiUrl) {
    extra.apiUrl = envApiUrl.replace(/\/+$/, '');
  } else if (extra.apiUrl) {
    delete extra.apiUrl;
  }

  return {
    ...appJson,
    expo: {
      ...baseExpoConfig,
      extra,
    },
  };
};
