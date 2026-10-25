// Import test modules into one Node process so tests also run in environments
// that restrict the subprocess workers used by `node --test`.
await import('../tests/persistence.test.mjs');
await import('../tests/p02-delivery-classifier.test.mjs');
await import('../tests/p02-delivery-boundary.test.mjs');
