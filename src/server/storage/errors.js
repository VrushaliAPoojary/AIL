export class AppError extends Error {
  constructor(message, status = 500, code = 'PERSISTENCE_ERROR', details = undefined) {
    super(message);
    this.name = 'AppError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class ValidationError extends AppError {
  constructor(message, details = undefined) {
    super(message, 400, 'VALIDATION_ERROR', details);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends AppError {
  constructor(message, details = undefined) {
    super(message, 404, 'NOT_FOUND', details);
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends AppError {
  constructor(message, details = undefined) {
    super(message, 409, 'CONFLICT', details);
    this.name = 'ConflictError';
  }
}

export class ConfigurationError extends AppError {
  constructor(message, details = undefined) {
    super(message, 503, 'CONFIGURATION_ERROR', details);
    this.name = 'ConfigurationError';
  }
}

export class PersistenceError extends AppError {
  constructor(message, status = 500, details = undefined) {
    super(message, status, 'PERSISTENCE_ERROR', details);
    this.name = 'PersistenceError';
  }
}


export class ResourceFileTooLargeError extends ValidationError {
  constructor(message = 'Resource file is too large.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileTooLargeError';
    this.status = 413;
    this.code = 'RESOURCE_FILE_TOO_LARGE';
  }
}

export class ResourceFileTypeUnsupportedError extends ValidationError {
  constructor(message = 'Resource file type is unsupported.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileTypeUnsupportedError';
    this.status = 415;
    this.code = 'RESOURCE_FILE_TYPE_UNSUPPORTED';
  }
}

export class ResourceFileSizeMismatchError extends ValidationError {
  constructor(message = 'Resource file size does not match the received bytes.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileSizeMismatchError';
    this.code = 'RESOURCE_FILE_SIZE_MISMATCH';
  }
}

export class ResourceFileAlreadyExistsError extends ConflictError {
  constructor(message = 'Resource file already exists.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileAlreadyExistsError';
    this.code = 'RESOURCE_FILE_ALREADY_EXISTS';
  }
}

export class ResourceFileIntegrityError extends ValidationError {
  constructor(message = 'Resource file integrity check failed.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileIntegrityError';
    this.status = 500;
    this.code = 'RESOURCE_FILE_INTEGRITY_FAILURE';
  }
}

export class ResourceFileNotFoundError extends NotFoundError {
  constructor(message = 'Resource file not found.', details = undefined) {
    super(message, details);
    this.name = 'ResourceFileNotFoundError';
    this.code = 'RESOURCE_FILE_NOT_FOUND';
  }
}
