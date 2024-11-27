export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  profile_picture_url: string | null;
}

export interface Group {
  id: number;
  name: string;
  description: string;
  created_by: number;
  members: User[];
}

export interface Expense {
  id: number;
  group_id: number;
  amount: number;
  description: string;
  paid_by_id: number;
  created_at: string;
  receipt_url?: string | null;
  splits: ExpenseSplit[];
}

export interface ExpenseSplit {
  id: number;
  expense_id: number;
  user_id: number;
  amount: number;
  user?: User;
}

export interface Balance {
  user_id: number;
  amount: number;
  user?: User;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
}
