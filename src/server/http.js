import { NextResponse } from 'next/server.js';
import { AppError } from './storage/errors.js';

export async function readJsonBody(request) {
  try {
    return await request.json();
  } catch {
    throw new AppError('Request body must be valid JSON.', 400, 'INVALID_JSON');
  }
}

export function errorResponse(error, fallbackMessage = 'Unable to save contribution.') {
  if (error instanceof AppError) {
    return NextResponse.json(
      {
        error: error.message,
        code: error.code,
        ...(error.details ? { details: error.details } : {}),
      },
      { status: error.status },
    );
  }

  console.error('[API Error]', error);

  return NextResponse.json(
    {
      error: error instanceof Error ? error.message : fallbackMessage,
    },
    { status: 500 },
  );
}
