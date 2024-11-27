export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  profile_picture_url: string | null;
}

export interface Group {
  id: string;
  name: string;
  description: string;
  created_by: string;
  members: User[];
}

export interface Expense {
  id: string;
  group_id: string;
  amount: number;
  description: string;
  paid_by_id: string;
  created_at: string;
  receipt_url?: string | null;
  splits: ExpenseSplit[];
}

export interface ExpenseSplit {
  id: string;
  expense_id: string;
  user_id: string;
  amount: number;
  user?: User;
}

export interface Balance {
  user_id: string;
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
