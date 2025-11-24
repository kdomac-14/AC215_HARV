const { FlatCompat } = require('@eslint/eslintrc');
const js = require('@eslint/js');
const stylisticTs = require('@stylistic/eslint-plugin-ts');

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const legacyConfigs = compat.config({
  extends: ['@react-native/eslint-config'],
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
});

let funcCallSpacingSetting;

const sanitizedLegacyConfigs = legacyConfigs.map(config => {
  if (
    config.rules &&
    Object.prototype.hasOwnProperty.call(
      config.rules,
      '@typescript-eslint/func-call-spacing'
    )
  ) {
    if (funcCallSpacingSetting === undefined) {
      funcCallSpacingSetting =
        config.rules['@typescript-eslint/func-call-spacing'];
    }
    const { ['@typescript-eslint/func-call-spacing']: _ignored, ...rest } =
      config.rules;
    return {
      ...config,
      rules: rest,
    };
  }
  return config;
});

const tsSpacingOverride =
  funcCallSpacingSetting !== undefined
    ? [
        {
          files: ['**/*.ts', '**/*.tsx'],
          plugins: {
            '@stylistic/ts': stylisticTs,
          },
          rules: {
            '@stylistic/ts/func-call-spacing': funcCallSpacingSetting,
          },
        },
      ]
    : [];

module.exports = [js.configs.recommended, ...sanitizedLegacyConfigs, ...tsSpacingOverride];
