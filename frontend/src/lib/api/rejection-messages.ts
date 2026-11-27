/** `rejection_codes` from contracts/error-codes.json. Keep in sync; the parity test checks it. */
export const REJECTION_CODES = [
  "FILE_EMPTY",
  "FILE_SIZE_MISMATCH",
  "FILE_TYPE_UNSUPPORTED",
  "FILE_CORRUPT",
  "ZIP_ENCRYPTED",
  "ZIP_TOO_MANY_MEMBERS",
  "ZIP_TOO_LARGE",
  "ZIP_RATIO_EXCEEDED",
  "ZIP_NESTED",
  "ZIP_UNSAFE_PATH",
  "ZIP_SYMLINK",
  "ZIP_MEMBER_UNSUPPORTED",
] as const;

export type RejectionCode = (typeof REJECTION_CODES)[number];

const REJECTION_MESSAGE_KEYS: {
  readonly [K in RejectionCode]: `errors.rejection.${K}`;
} = Object.fromEntries(
  REJECTION_CODES.map((code) => [code, `errors.rejection.${code}`]),
) as never;

/** Exported for the parity test; not meant for other callers. */
export { REJECTION_MESSAGE_KEYS };

/** `File.rejection_code` (set on `complete` when `status` is `rejected`) -> next-intl message key. */
export function mapRejectionCode(code: RejectionCode): string {
  return REJECTION_MESSAGE_KEYS[code];
}
