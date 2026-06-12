def public_upload_path(path: str | None) -> str | None:
    if path is None:
        return None
    normalized = str(path).strip().replace('\\', '/')
    if not normalized:
        return normalized

    marker = '/uploads/'
    marker_index = normalized.find(marker)
    if marker_index >= 0:
        return normalized[marker_index:]
    if normalized.startswith('uploads/'):
        return '/' + normalized
    return normalized
