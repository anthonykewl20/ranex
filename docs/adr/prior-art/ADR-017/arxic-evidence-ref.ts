import { readFileSync } from 'node:fs';
import Ajv2020, { type ErrorObject } from 'ajv/dist/2020';
import addFormats from 'ajv-formats';
import {
  ARXIC_EVIDENCE_REF_INVALID,
  ARXIC_EVIDENCE_REF_KIND_UNKNOWN,
  ARXIC_EVIDENCE_REF_RANGE,
  type Diagnostic,
} from './diagnostics';

export type EvidenceRefSource = {
  kind: 'source';
  repo: string;
  commit: string;
  path: string;
  startLine: number;
  endLine: number;
  blobSha256: string;
  extractor: string;
  ruleId?: string;
};

export type EvidenceRefRuntime = {
  kind: 'runtime';
  runId: string;
  appBuildDigest: string;
  browser: string;
  browserVersion: string;
  url: string;
  timestamp: string;
  accessibilitySnapshotSha256?: string;
  screenshotRef?: string;
  traceRef?: string;
  networkRefs?: string[];
};

export type EvidenceRefDocument = {
  kind: 'document';
  artifactRef: string;
  section?: string;
  sha256: string;
};

export type EvidenceRef = EvidenceRefSource | EvidenceRefRuntime | EvidenceRefDocument;

const schemaUrl = new URL('../../../schemas/evidence/evidence-ref.schema.json', import.meta.url);
let evidenceRefSchema: object;

try {
  evidenceRefSchema = JSON.parse(readFileSync(schemaUrl, 'utf8')) as object;
} catch (error) {
  throw new Error(`Failed to load EvidenceRef schema at ${schemaUrl.pathname}`, { cause: error });
}

const ajv = new Ajv2020({ allErrors: true, $data: true });
addFormats(ajv);
const validate = ajv.compile<EvidenceRef>(evidenceRefSchema);

const isRecord = (input: unknown): input is Record<string, unknown> =>
  typeof input === 'object' && input !== null && !Array.isArray(input);

const diagnosticCode = (input: unknown) => {
  if (!isRecord(input) || !['source', 'runtime', 'document'].includes(String(input.kind))) {
    return ARXIC_EVIDENCE_REF_KIND_UNKNOWN;
  }
  if (
    input.kind === 'source' &&
    typeof input.startLine === 'number' &&
    typeof input.endLine === 'number' &&
    input.startLine > input.endLine
  ) {
    return ARXIC_EVIDENCE_REF_RANGE;
  }
  return ARXIC_EVIDENCE_REF_INVALID;
};

const toDiagnostic = (error: ErrorObject, code: string): Diagnostic => ({
  code,
  severity: 'blocked',
  subject: 'evidence-ref',
  message: `${error.instancePath || '/'} ${error.message ?? 'is invalid'}`,
});

export const validateEvidenceRef = (
  input: unknown,
): { ok: true; value: EvidenceRef } | { ok: false; diagnostics: Diagnostic[] } => {
  if (validate(input)) {
    return { ok: true, value: input };
  }
  const code = diagnosticCode(input);
  return {
    ok: false,
    diagnostics: (validate.errors ?? []).map((error) => toDiagnostic(error, code)),
  };
};
