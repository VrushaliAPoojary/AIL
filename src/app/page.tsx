import type { Metadata } from 'next';
import { DeliveryControlCenter } from '../features/delivery/DeliveryControlCenter';

export const metadata: Metadata = {
  title: 'ERPNext Supplier Delivery & Delay Control Center',
  description: 'Supplier Delivery Confirmation & Delay Escalation for ERPNext',
};

export default function Page() {
  return <DeliveryControlCenter />;
}
