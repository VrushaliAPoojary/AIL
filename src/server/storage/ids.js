import { randomBytes } from 'node:crypto';

const CROCKFORD_BASE32 = '0123456789abcdefghjkmnpqrstvwxyz';

function encodeUlid(buffer) {
  let value = BigInt(`0x${Buffer.from(buffer).toString('hex')}`);
  let output = '';

  for (let index = 0; index < 26; index += 1) {
    const digit = Number(value % 32n);
    output = CROCKFORD_BASE32[digit] + output;
    value /= 32n;
  }

  return output;
}

export function createRecordId(prefix) {
  const timestamp = Buffer.alloc(6);
  timestamp.writeUIntBE(Date.now(), 0, 6);
  const entropy = randomBytes(10);
  return `${prefix}_${encodeUlid(Buffer.concat([timestamp, entropy]))}`;
}
