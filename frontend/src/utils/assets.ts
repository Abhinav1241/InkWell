/**
 * Resolves storage URIs (e.g. gs://bucket/path/to/file.png) to browser-loadable HTTP URLs.
 */
export function resolveAssetUri(uri?: string | null): string | undefined {
  if (!uri) return undefined;
  if (uri.startsWith('gs://')) {
    // Strip gs://bucket-name/ -> /media/path/to/file.png
    const withoutScheme = uri.replace(/^gs:\/\//, '');
    const parts = withoutScheme.split('/');
    parts.shift(); // Remove bucket name
    return `/media/${parts.join('/')}`;
  }
  return uri;
}
