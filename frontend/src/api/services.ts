import client from './client';
import axios from 'axios';
import { User, Group, Expense, AuthResponse, ExpenseCreate } from '../types';

const API_URL = 'http://localhost:8000';

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
  getGroups: async (): Promise<Group[]> => {
    const response = await client.get('/groups');
    return response.data;
  },

  getGroup: async (groupId: number): Promise<Group> => {
    const response = await client.get(`/groups/${groupId}`);
    return response.data;
  },

  createGroup: async (groupData: { name: string; description: string }): Promise<Group> => {
    const response = await client.post('/groups', groupData);
    return response.data;
  },

  addMember: async (groupId: number, userId: number): Promise<void> => {
    await client.post(`/groups/${groupId}/members/${userId}`);
  },

  deleteGroup: async (groupId: number): Promise<void> => {
    await client.delete(`/groups/${groupId}`);
  },
};

export const expenseService = {
  createExpense: async (groupId: number, expenseData: {
    amount: number;
    description: string;
    paid_by_id: number;
    splits: { user_id: number; amount: number }[];
  }): Promise<Expense> => {
    const { data } = await client.post<Expense>(`/groups/${groupId}/expenses/`, {
      ...expenseData,
      group_id: groupId
    });
    return data;
  },

  getGroupExpenses: async (groupId: number): Promise<Expense[]> => {
    const { data } = await client.get<Expense[]>(`/groups/${groupId}/expenses`);
    return data;
  },

  getGroupBalances: async (groupId: number): Promise<{ [key: number]: number }> => {
    const { data } = await client.get<{ [key: number]: number }>(`/groups/${groupId}/expenses/balances`);
    return data;
  },

  getExpenseDetails: async (groupId: number, expenseId: number): Promise<Expense> => {
    const response = await client.get<Expense>(`/groups/${groupId}/expenses/${expenseId}`);
    return response.data;
  },

  uploadReceipt: async (groupId: number, expenseId: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await client.post(
      `/groups/${groupId}/expenses/${expenseId}/receipt`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    
    // Prepend API_URL to the receipt_url if it's a relative path
    const receipt_url = response.data.receipt_url.startsWith('http') 
      ? response.data.receipt_url 
      : `${API_URL}${response.data.receipt_url}`;
    
    return { receipt_url };
  },

  deleteExpense: async (groupId: number, expenseId: number): Promise<void> => {
    await client.delete(`/groups/${groupId}/expenses/${expenseId}`);
  },
};

interface Settlement {
  paid_by_id: number;
  paid_to_id: number;
  amount: number;
  group_id: number;
}

interface GroupBalances {
  balances: Array<{
    user_id: number;
    user_name: string;
    balance: number;
  }>;
  suggested_settlements: Array<{
    paid_by_id: number;
    paid_by_name: string;
    paid_to_id: number;
    paid_to_name: string;
    amount: number;
  }>;
}

export const settlementService = {
  createSettlement: async (settlement: Settlement): Promise<any> => {
    const { data } = await client.post('/settlements', settlement);
    return data;
  },

  getGroupBalances: async (groupId: number): Promise<GroupBalances> => {
    const { data } = await client.get(`/settlements/group/${groupId}/balances`);
    return data;
  },
};
