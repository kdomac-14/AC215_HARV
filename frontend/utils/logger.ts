/* eslint-disable no-console */

const shouldLog = typeof __DEV__ !== 'undefined' ? __DEV__ : true;

export const logError = (...args: unknown[]) => {
  if (shouldLog) {
    console.error(...args);
  }
};

export const logWarn = (...args: unknown[]) => {
  if (shouldLog) {
    console.warn(...args);
  }
};

export const logInfo = (...args: unknown[]) => {
  if (shouldLog) {
    console.info(...args);
  }
};

export const logDebug = (...args: unknown[]) => {
  if (shouldLog) {
    console.debug(...args);
  }
};
