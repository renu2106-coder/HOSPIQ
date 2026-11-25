/**
 * Strips Markdown formatting symbols (hashtags #, ##, ### and stars *, **)
 * so clinical documents always render as clean plain text.
 */
export function stripReportMarkdown(raw: string | undefined | null): string {
  if (!raw) return '';
  return raw
    .split('\n')
    .map((line) => {
      // Remove leading heading hashes (#, ##, ###, etc.)
      let clean = line.replace(/^\s*#{1,6}\s*/g, '');
      // Convert leading markdown bullets (* item or - item) to clean bullet character (keep --- dividers intact)
      if (!/^\s*-{3,}\s*$/.test(clean)) {
        clean = clean.replace(/^(\s*)[-*]\s+/g, '$1• ');
      }
      // Remove bold/italic asterisks
      clean = clean.replace(/\*\*\*/g, '').replace(/\*\*/g, '').replace(/\*/g, '');
      return clean;
    })
    .join('\n');
}
