export interface User {
  id: string;
  email: string;
  full_name: string;
  profile_picture_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Group {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  members: User[];
}

export interface ExpenseSplit {
  id: string;
  expense_id: string;
  user_id: string;
  amount: number;
  user?: User;
  is_settled: boolean;
}

export interface Expense {
  id: string;
  amount: number;
  description: string;
  date: string;
  paid_by_id: string;
  group_id: string;
  receipt_url?: string;
  splits: ExpenseSplit[];
  paid_by?: User;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  amount: number;
  description: string;
  paid_by_id: string;
  group_id: string;
  splits: {
    user_id: string;
    amount: number;
  }[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Settlement {
  id: string;
  paid_by_id: string;
  paid_to_id: string;
  amount: number;
  group_id: string;
  created_at: string;
  updated_at: string;
}

export interface SettlementCreate {
  paid_by_id: string;
  paid_to_id: string;
  amount: number;
  group_id: string;
}

export interface GroupBalance {
  user_id: string;
  user_name: string;
  profile_picture_url?: string;
  balance: number;
}

export interface SuggestedSettlement {
  paid_by_id: string;
  paid_by_name: string;
  paid_to_id: string;
  paid_to_name: string;
  amount: number;
}

export interface GroupSettlementSummary {
  balances: GroupBalance[];
  suggested_settlements: SuggestedSettlement[];
}

export interface BalancesResponse {
  balances: GroupBalance[];
  suggested_settlements: SuggestedSettlement[];
}
