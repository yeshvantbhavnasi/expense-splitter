import client from './client';
import axios from 'axios';
import { User, Group, Expense, AuthResponse, ExpenseCreate, Settlement, SettlementCreate, GroupBalances, BalancesResponse, GroupSettlementSummary } from '../types';

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

  uploadProfilePicture: async (file: File): Promise<User> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await client.post<User>('/users/me/profile-picture', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return data;
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
  createExpense(groupId: string, expenseData: ExpenseCreate): Promise<Expense> {
    return client.post(
      `/groups/${groupId}/expenses/`,
      expenseData
    ).then(response => response.data);
  },

  getGroupExpenses(groupId: string): Promise<Expense[]> {
    return client.get(`/groups/${groupId}/expenses/`)
      .then(response => response.data);
  },

  getGroupBalances(groupId: string): Promise<GroupSettlementSummary> {
    return client.get(`/groups/${groupId}/expenses/balances`)
      .then(response => response.data);
  },

  getExpenseDetails(groupId: string, expenseId: string): Promise<Expense> {
    return client.get(`/groups/${groupId}/expenses/${expenseId}`)
      .then(response => response.data);
  },

  uploadReceipt(groupId: string, expenseId: string, file: File): Promise<Expense> {
    const formData = new FormData();
    formData.append('file', file);

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

export const settlementService = {
  createSettlement(settlement: SettlementCreate): Promise<Settlement> {
    return client.post('/settlements/', settlement)
      .then(response => response.data);
  },

  getGroupBalances(groupId: string): Promise<GroupSettlementSummary> {
    return client.get(`/settlements/group/${groupId}/balances`)
      .then(response => response.data);
  },
};
