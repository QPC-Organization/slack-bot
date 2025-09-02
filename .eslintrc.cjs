module.exports = {
  extends: ['next/core-web-vitals'],
  parserOptions: {
    babelOptions: {
      presets: [require.resolve('next/babel')],
    },
  },
  rules: {
    // Add custom ESLint rules here
  },
};
