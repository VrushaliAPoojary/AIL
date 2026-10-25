import type { Metadata } from 'next';
import { DeliveryControlCenter } from '../../features/delivery/DeliveryControlCenter';

export const metadata: Metadata = {
  title: 'P02 Delivery Control Center',
  description: 'Supplier Delivery Confirmation & Delay Escalation',
};

export default function DeliveryPage() {
  return <DeliveryControlCenter />;
}
