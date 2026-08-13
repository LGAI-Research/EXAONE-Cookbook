const escapeHtml = (text: string) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')

/**
 * Content data is authored in plain text with Markdown-style inline code.
 * Escape first, then promote backticks — the strings contain things like
 * `custom:exaone/<model>` that must not be parsed as HTML.
 */
export const inlineCode = (text: string) =>
  escapeHtml(text).replace(/`([^`]+)`/g, '<code>$1</code>')
