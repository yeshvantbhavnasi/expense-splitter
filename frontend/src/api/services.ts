import client from './client';
import axios from 'axios';
import { User, Group, Expense, AuthResponse, ExpenseCreate } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const axiosInstance = axios.create({
  baseURL: API_URL,
});

export const authService = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);  // The backend expects 'username' for email
    formData.append('password', password);

    const response = await client.post('/token', formData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    });

    if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
    }

    return response.data;
  },

  register: async (userData: {
    email: string;
    password: string;
    username: string;
    full_name: string;
  }): Promise<User> => {
    const { data } = await client.post<User>('/users/', userData);
    return data;
  },
};

export const userService = {
  getCurrentUser: async (): Promise<User> => {
    const { data } = await client.get<User>('/users/me');
    return data;
  },

  searchUsers: async (query: string): Promise<User[]> => {
    const { data } = await client.get<User[]>(`/users/search?q=${encodeURIComponent(query)}`);
    return data;
  },

  updateProfile: async (userData: { full_name: string }): Promise<User> => {
    const { data } = await client.patch<User>('/users/me', userData);
    return data;
  },

  uploadProfilePicture: async (file: File): Promise<{ url: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await client.post('/users/me/profile-picture', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    // Prepend API_URL to the URL if it's a relative path
    const url = response.data.url.startsWith('http') 
      ? response.data.url 
      : `${API_URL}${response.data.url}`;
    
    return { url };
  },

  updatePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await client.post('/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};

export const groupService = {
  getGroups(): Promise<Group[]> {
    return client.get<Group[]>('/groups/').then(response => response.data);
  },

  getGroup(groupId: string): Promise<Group> {
    return client.get<Group>(`/groups/${groupId}`).then(response => response.data);
  },

  createGroup(groupData: { name: string; description: string }): Promise<Group> {
    return client.post<Group>('/groups/', groupData).then(response => response.data);
  },

  addMember(groupId: string, userId: string): Promise<void> {
    return client.post(`/groups/${groupId}/members/${userId}`);
  },

  deleteGroup(groupId: string): Promise<void> {
    return client.delete(`/groups/${groupId}`);
  },
};

export const expenseService = {
  createExpense(groupId: string, expenseData: {
    amount: number;
    description: string;
    paid_by_id: string;
    splits: { user_id: string; amount: number }[];
  }): Promise<Expense> {
    const data = {
      ...expenseData,
      group_id: groupId
    };
    return client.post<Expense>(`/groups/${groupId}/expenses/`, data)
      .then(response => response.data);
  },

  getGroupExpenses(groupId: string): Promise<Expense[]> {
    return client.get<Expense[]>(`/groups/${groupId}/expenses/`)
      .then(response => response.data);
  },

  getGroupBalances(groupId: string): Promise<{ [key: string]: number }> {
    return client.get(`/groups/${groupId}/expenses/balances`)
      .then(response => response.data);
  },

  getExpenseDetails(groupId: string, expenseId: string): Promise<Expense> {
    return client.get<Expense>(`/groups/${groupId}/expenses/${expenseId}`)
      .then(response => response.data);
  },

  uploadReceipt(groupId: string, expenseId: string, file: File) {
    const formData = new FormData();
    formData.append('receipt', file);

    return client.post(
      `/groups/${groupId}/expenses/${expenseId}/receipt`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    ).then(response => response.data);
  },

  deleteExpense(groupId: string, expenseId: string): Promise<void> {
    return client.delete(`/groups/${groupId}/expenses/${expenseId}`);
  },
};

interface Settlement {
  paid_by_id: string;
  paid_to_id: string;
  amount: number;
  group_id: string;
}

interface GroupBalances {
  balances: Array<{
    user_id: string;
    user_name: string;
    balance: number;
  }>;
  suggested_settlements: Array<{
    paid_by_id: string;
    paid_by_name: string;
    paid_to_id: string;
    paid_to_name: string;
    amount: number;
  }>;
}

export const settlementService = {
  createSettlement(settlement: Settlement): Promise<any> {
    return client.post('/settlements/', settlement)
      .then(response => response.data);
  },

  getGroupBalances(groupId: string): Promise<GroupBalances> {
    return client.get(`/settlements/group/${groupId}/balances`)
      .then(response => response.data);
  },
};
