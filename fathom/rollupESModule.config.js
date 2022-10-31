// Bundle all of Fathom into a single file for use inside web extensions or
// other applications. If possible, use ES6-style import statements in your
// code instead, and let rollup pull in just what Fathom code is necessary. See
// /fathom_fox/rollup.config.js for an example.
export default {
  input: 'index.mjs',
  output: {
    file: 'dist/fathom.mjs',
    format: 'esm',
    name: 'fathom',
  }
};
