export interface Expedition {
  id: number;
  name: string;
  owner_chat_id: number;
  status: ExpeditionStatus;
  deadline?: string;
  created_at?: string;
  completed_at?: string;
  description?: string;
}

export interface ExpeditionDetails extends Expedition {
  items: ExpeditionItem[];
  consumptions: ItemConsumption[];
  progress: ExpeditionProgress;
}

export interface ExpeditionItem {
  id: number;
  product_id: number;
  product_name: string;
  product_emoji?: string;
  quantity: number;           // Total quantity needed (same as quantity_needed)
  quantity_needed: number;
  consumed: number;            // Quantity consumed (same as quantity_consumed)
  quantity_consumed: number;
  available: number;           // Available quantity (quantity_needed - consumed)
  unit_price: number;
  price: number;               // Unit price (same as unit_price)
  added_at?: string;
  quality_grade?: QualityGrade;
}

export interface ItemConsumption {
  id: number;
  consumer_name: string;
  pirate_name: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  amount_paid: number;
  payment_status: PaymentStatus;
  consumed_at?: string;
  expedition_id?: number;
  expedition_name?: string;
}

export interface ExpeditionProgress {
  total_items: number;
  consumed_items: number;
  remaining_items: number;
  completion_percentage: number;
  total_value: number;
  consumed_value: number;
  remaining_value: number;
}

export interface CreateExpeditionRequest {
  name: string;
  deadline?: string;
  description?: string;
}

export interface CreateExpeditionItemRequest {
  items: {
    product_id: number;
    quantity: number;
    quality_grade?: QualityGrade;
    unit_cost?: number;
  }[];
}

export interface ConsumeItemRequest {
  product_id: number;
  pirate_name: string;
  quantity: number;
  price: number;
}

export interface PayConsumptionRequest {
  consumption_id: number;
  amount: number;
}

export interface PirateStats {
  total_items: number;
  items_consumed: number;
  total_spent: number;
  total_paid: number;
  debt: number;
}

export interface RecentItem {
  name: string;
  emoji: string;
  quantity: number;
  consumed_at: string | null;
}

export interface PirateName {
  id: number;
  expedition_id: number;
  original_name?: string; // Only visible to owner
  pirate_name: string;
  created_at?: string;
  stats: PirateStats;
  recent_items: RecentItem[];
}

export interface Buyer {
  name: string;
}

export interface BramblerGenerateRequest {
  original_names: string[];
}

export interface BramblerDecryptRequest {
  owner_key: string;
}

export interface DashboardStats {
  total_expeditions: number;
  active_expeditions: number;
  completed_expeditions: number;
  overdue_expeditions: number;
}

export interface TimelineData {
  timeline: ExpeditionTimelineEntry[];
  stats: DashboardStats;
}

export interface ExpeditionTimelineEntry extends Expedition {
  is_overdue: boolean;
  progress: ExpeditionProgress;
}

export interface AnalyticsData {
  overview: {
    total_expeditions: number;
    active_expeditions: number;
    completed_expeditions: number;
    cancelled_expeditions: number;
    overdue_expeditions: number;
  };
  value_analysis: {
    total_expedition_value: number;
    completed_expedition_value: number;
    active_expedition_value: number;
    consumed_value: number;
    pending_value: number;
  };
  progress_analysis: {
    average_completion_rate: number;
    expeditions_by_progress: {
      '0-25%': number;
      '25-50%': number;
      '50-75%': number;
      '75-100%': number;
      completed: number;
    };
  };
  timeline_analysis: {
    expeditions_created_this_week: number;
    expeditions_created_this_month: number;
    expeditions_completed_this_week: number;
    expeditions_completed_this_month: number;
  };
}

export type ExpeditionStatus = 'active' | 'completed' | 'cancelled';
export type PaymentStatus = 'pending' | 'paid' | 'partial';
export type QualityGrade = 'A' | 'B' | 'C';
export type AlertLevel = 'info' | 'warning' | 'urgent' | 'critical';

export interface Product {
  id: number;
  name: string;
  emoji?: string;
  price: number;
  stock: number;
  status: string;
}

export interface WebSocketUpdate {
  type: 'ITEM_CONSUMED' | 'EXPEDITION_COMPLETED' | 'DEADLINE_WARNING' | 'EXPEDITION_CREATED' | 'EXPEDITION_UPDATED';
  expedition_id?: number;
  expedition_name?: string;
  pirate_name?: string;
  item_name?: string;
  consumer_name?: string;
  message?: string;
  timestamp: string;
}