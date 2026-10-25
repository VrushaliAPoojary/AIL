import { Suspense } from 'react';
import { Walkthrough } from '../../features/core/walkthrough/Walkthrough';

export default function WalkthroughPage() {
  return (
    <Suspense fallback={<div>Loading walkthrough...</div>}>
      <Walkthrough />
    </Suspense>
  );
}
