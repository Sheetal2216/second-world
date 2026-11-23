
export interface Project {
  id: number;
  name: string;
  description: string | null;
}

export interface Dataset {
  id: number;
  project_id: number;
  filename: string;
  file_type: string;
  storage_path: string;
  status: string;
  parsed_data: Record<string, unknown> | null;
  created_at: string;
}

export interface WorldConfig {
  schema_version: number;
  cafe_name: string;
  currency: string;
  seating_capacity: number | null;

  operating_hours: {
    day_type: "weekday" | "weekend";
    open_hour: number;
    close_hour: number;
  }[];

  staff: {
    role: string;
    count: number;
    hourly_wage: number | null;
    duties: "order_taking" | "preparation" | "both";
  }[];

  menu: {
    name: string;
    category: string | null;
    price: number;
    unit_cost: number | null;
    prep_time_seconds: number | null;
    popularity_share: number | null;
    ingredients: {
      ingredient: string;
      quantity: number;
    }[];
  }[];

  inventory: {
    ingredient: string;
    unit: string;
    starting_quantity: number | null;
    unit_cost: number | null;
    reorder_level: number | null;
  }[];

  demand: {
    day_type: "weekday" | "weekend";
    hour: number;
    avg_arrivals: number;
  }[];

  demand_modifiers: {
    description: string;
    day_type: "weekday" | "weekend";
    start_hour: number;
    end_hour: number;
    multiplier: number;
  }[];

  customer_behavior: {
    avg_patience_minutes: number | null;
    avg_items_per_order: number | null;
  };

  assumptions: {
    field_path: string;
    assumed_value: string;
    reason: string;
  }[];

  missing_information: {
    field_path: string;
    why_needed: string;
  }[];

  source_dataset_ids: number[];
}

export interface World {
  id: number;
  project_id: number;
  name: string;
  parent_world_id: number | null;
  change_summary: string | null;
  config_json: WorldConfig;
  is_baseline: boolean;
  created_at: string;
}

export interface SimulationSummary {
  customers_arrived: number;
  orders_served: number;
  abandoned: number;
  abandonment_rate: number;
  stockout_items: number;
  revenue: number;
  lost_revenue: number;
  ingredient_cost: number;
  staff_cost: number;
  profit: number;
  avg_wait_min: number;
  p90_wait_min: number;
  max_wait_min: number;
  staff_utilization: number;
  ingredients_consumed: Record<string, number>;
}

export interface TimeseriesPoint {
  minute: number;
  clock_hour: number;
  queue_length: number;
  staff_busy: number;
  revenue: number;
  served: number;
  abandoned: number;
}

export interface SimulationResults {
  summary: SimulationSummary;
  timeseries: TimeseriesPoint[];
  assumptions_used: string[];
  day_type: "weekday" | "weekend";
}

export interface Simulation {
  id: number;
  world_id: number;
  status: string;
  random_seed: number | null;
  results_json: SimulationResults;
  started_at: string | null;
  completed_at: string;
}
