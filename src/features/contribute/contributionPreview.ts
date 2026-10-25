export function summarizeContributionResource(contribution: {
  type: string;
  resource: {
    url?: string;
    text?: string;
    file?: {
      name: string;
      mime_type?: string;
      size?: number;
    };
  };
}) {
  const resource = contribution.resource || {};
  if (contribution.type === 'LINK') {
    try {
      const url = new URL(resource.url || '');
      return `${url.hostname.replace(/^www\./, '')}${url.pathname}`;
    } catch {
      return resource.url || 'Link';
    }
  }
  if (contribution.type === 'TEXT' || contribution.type === 'INSIGHT') {
    const text = String(resource.text || '').trim();
    return text.length > 120 ? `${text.slice(0, 117)}...` : text || 'Text';
  }
  if (resource.file?.name) {
    return resource.file.name;
  }
  return 'File';
}
