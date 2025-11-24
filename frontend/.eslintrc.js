module.exports = {
  extends: ['@react-native/eslint-config', 'eslint:recommended'],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
  },
  env: {
    es6: true,
    browser: true,
    node: true,
  },
  rules: {
    'no-console': 'warn',
  },
};
