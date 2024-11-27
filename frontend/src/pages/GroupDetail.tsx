import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import { groupService, expenseService, settlementService } from '../api/services';
import { Group, Expense, Balance, User, GroupBalances } from '../types';
import { PlusIcon, UserPlusIcon, TrashIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import AddMemberModal from '../components/AddMemberModal';
import ProfilePicture from '../components/ProfilePicture';
import ReceiptIcon from '../components/ReceiptIcon';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:8000';

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const [group, setGroup] = useState<Group | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [balances, setBalances] = useState<GroupBalances | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [splitType, setSplitType] = useState<'equal' | 'custom' | 'percentage'>('equal');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [newExpense, setNewExpense] = useState({
    amount: '',
    description: '',
    paidById: 0, // This will be set to current user's ID once loaded
    splits: [] as { user_id: number; amount: string }[],
  });
  const [selectedReceipt, setSelectedReceipt] = useState<File | null>(null);
  const [showSettleModal, setShowSettleModal] = useState(false);
  const [selectedSettlement, setSelectedSettlement] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (user) {
      setCurrentUser(user);
      setNewExpense(prev => ({ ...prev, paidById: user.id }));
    }
  }, []);

  useEffect(() => {
    if (id) {
      fetchGroupData();
    }
  }, [id]);

  useEffect(() => {
    if (group) {
      fetchBalances();
    }
  }, [group]);

  const fetchGroupData = async () => {
    try {
      const [groupData, expensesData, balancesData] = await Promise.all([
        groupService.getGroup(Number(id)),
        expenseService.getGroupExpenses(Number(id)),
        settlementService.getGroupBalances(Number(id)),
      ]);
      setGroup(groupData);
      setExpenses(expensesData);
      setBalances(balancesData);
    } catch (err) {
      setError('Failed to fetch group data');
    } finally {
      setLoading(false);
    }
  };

  const fetchBalances = async () => {
    try {
      const data = await settlementService.getGroupBalances(Number(id));
      setBalances(data);
    } catch (err) {
      console.error('Error fetching balances:', err);
    }
  };

  const handleCreateExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!group) return;

    try {
      const totalSplit = newExpense.splits.reduce(
        (sum, split) => sum + parseFloat(split.amount), 
        0
      );

      if (Math.abs(totalSplit - parseFloat(newExpense.amount)) > 0.01) {
        setError('Split amounts must equal the total expense amount');
        return;
      }

      const expenseResponse = await expenseService.createExpense(Number(id), {
        amount: parseFloat(newExpense.amount),
        description: newExpense.description,
        paid_by_id: newExpense.paidById,
        splits: newExpense.splits.map(split => ({
          user_id: split.user_id,
          amount: parseFloat(split.amount)
        }))
      });

      // Upload receipt if selected
      if (selectedReceipt && expenseResponse.id) {
        try {
          const formData = new FormData();
          formData.append('file', selectedReceipt);
          
          await expenseService.uploadReceipt(Number(id), expenseResponse.id, selectedReceipt);
        } catch (uploadError) {
          console.error('Failed to upload receipt:', uploadError);
          setError('Expense created but failed to upload receipt');
          // Continue with closing the modal since the expense was created
        }
      }

      setShowExpenseModal(false);
      resetExpenseForm();
      await fetchGroupData();
    } catch (err) {
      console.error('Failed to create expense:', err);
      setError('Failed to create expense. Please try again.');
    }
  };

  const handleAddMember = async (userId: number) => {
    if (!group) return;
    try {
      await groupService.addMember(group.id, userId);
      await fetchGroupData(); // Refresh group data to get updated member list
    } catch (err) {
      setError('Failed to add member');
    }
  };

  const handleDeleteExpense = async (expenseId: number) => {
    try {
      await expenseService.deleteExpense(Number(id), expenseId);
      // Refresh the expenses list after deletion
      await fetchGroupData();
    } catch (err) {
      console.error('Failed to delete expense:', err);
      setError('Failed to delete expense. Please try again.');
    }
  };

  const handleDeleteGroup = async () => {
    try {
      if (!group) return;
      
      // Confirm deletion
      const confirmDelete = window.confirm(
        `Are you sure you want to delete the group "${group.name}"? This will remove all expenses and cannot be undone.`
      );
      
      if (!confirmDelete) return;

      // Delete the group
      await groupService.deleteGroup(group.id);
      
      // Redirect to dashboard after successful deletion
      navigate('/');
    } catch (err) {
      console.error('Failed to delete group:', err);
      setError('Failed to delete group. Please try again.');
    }
  };

  const initializeExpenseSplits = () => {
    if (!group) return;

    const amount = parseFloat(newExpense.amount) || 0;
    let splits: { user_id: number; amount: string }[] = [];

    switch (splitType) {
      case 'equal':
        { const splitAmount = (amount / group.members.length).toFixed(2);
        splits = group.members.map(member => ({
          user_id: member.id,
          amount: splitAmount
        }));
        break; }
      
      case 'percentage':
        { const percentPerPerson = (100 / group.members.length).toFixed(2);
        splits = group.members.map(member => ({
          user_id: member.id,
          amount: ((amount * parseFloat(percentPerPerson)) / 100).toFixed(2)
        }));
        break; }
      
      case 'custom':
        splits = group.members.map(member => ({
          user_id: member.id,
          amount: '0.00'
        }));
        break;
    }

    setNewExpense(prev => ({ ...prev, splits }));
  };

  const resetExpenseForm = () => {
    setNewExpense({
      amount: '',
      description: '',
      paidById: currentUser?.id || 0,
      splits: []
    });
    setSelectedReceipt(null);
    setSplitType('equal');
  };

  const handleCloseExpenseModal = () => {
    setShowExpenseModal(false);
    resetExpenseForm();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        setError('File size too large. Please select a file under 5MB.');
        return;
      }
      setSelectedReceipt(file);
      setError(''); // Clear any existing errors
    }
  };

  const handleSettle = async () => {
    if (!selectedSettlement) return;
    
    try {
      await settlementService.createSettlement({
        paid_by_id: selectedSettlement.paid_by_id,
        paid_to_id: selectedSettlement.paid_to_id,
        amount: selectedSettlement.amount,
        group_id: Number(id)
      });
      
      setShowSettleModal(false);
      setSelectedSettlement(null);
      fetchBalances();
      fetchGroupData();
    } catch (err) {
      console.error('Error settling balance:', err);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!group) {
    return (
      <DashboardLayout>
        <div className="text-center">
          <p className="text-red-500">Group not found</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="h-full flex flex-col py-6">
        <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {group?.name}
                {currentUser && group && currentUser.id === group.creator_id && (
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <ShieldCheckIcon className="h-4 w-4 mr-1" />
                    Admin
                  </span>
                )}
              </h1>
              {currentUser && group && currentUser.id === group.creator_id && (
                <button 
                  onClick={handleDeleteGroup}
                  className="text-red-500 hover:text-red-700 focus:outline-none ml-4"
                  aria-label="Delete group"
                >
                  <TrashIcon className="h-6 w-6" />
                </button>
              )}
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowAddMemberModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-500 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <UserPlusIcon className="h-5 w-5 mr-2" />
                Add Member
              </button>
              <button
                onClick={() => setShowExpenseModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-500 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Expense
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          <div className="mt-8 grid gap-8 lg:grid-cols-2">
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-medium text-gray-900 mb-4">Group Members</h2>
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {group.members.map((member) => (
                      <li key={member.id} className="flex items-center justify-between py-4 border-b last:border-b-0">
                        <div className="flex items-center space-x-4">
                          <ProfilePicture 
                            url={member.profile_picture_url} 
                            name={member.full_name} 
                            size="md" 
                          />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {member.full_name}
                            </p>
                            {group.creator_id === member.id && (
                              <div className="flex items-center space-x-1 text-green-600 text-xs mt-1">
                                <ShieldCheckIcon className="h-4 w-4" />
                                <span>Group Admin</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div>
                <h2 className="text-lg font-medium text-gray-900 mb-4">Balances</h2>
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200">
                    {balances && balances.balances.map((balance) => (
                      <li key={balance.user_id} className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <ProfilePicture
                              url={balance.profile_picture_url}
                              name={balance.user_name}
                              size="sm"
                              className="mr-3"
                            />
                            <p className="text-sm font-medium text-gray-900">{balance.user_name}</p>
                          </div>
                          <span
                            className={`text-sm font-medium ${
                              balance.balance >= 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {balance.balance >= 0 ? '+' : ''}${Math.abs(balance.balance).toFixed(2)}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Recent Expenses</h2>
              <div className="mt-8">
                <div className="flow-root">
                  {expenses.length > 0 ? (
                    <ul role="list" className="-mb-8">
                      {expenses.map((expense) => {
                        // Add additional null checks
                        const paidByUser = expense.paid_by || 
                          group?.members.find(m => m.id === expense.paid_by_id);
                        
                        // Skip rendering if critical data is missing
                        if (!paidByUser) {
                          console.warn('Skipping expense due to missing paid by user', expense);
                          return null;
                        }

                        return (
                          <li key={expense.id} className="py-4 border-b last:border-b-0">
                            <div className="flex items-center justify-between space-x-4">
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 truncate">
                                  {expense.description || 'Unnamed Expense'}
                                </p>
                                <p className="text-sm text-gray-500">
                                  Paid by {paidByUser.full_name || 'Unknown'}
                                </p>
                              </div>
                              <div className="flex items-center space-x-4">
                                <span className="text-sm font-medium text-gray-900">
                                  ${typeof expense.amount === 'number' 
                                    ? expense.amount.toFixed(2) 
                                    : parseFloat(expense.amount || '0').toFixed(2)}
                                </span>
                                <time 
                                  dateTime={expense.date ? new Date(expense.date).toISOString() : ''}
                                  className="text-sm text-gray-500"
                                >
                                  {expense.date 
                                    ? new Date(expense.date).toLocaleDateString() 
                                    : 'No Date'}
                                </time>
                                {currentUser && expense.paid_by_id === currentUser.id && (
                                  <button 
                                    onClick={() => handleDeleteExpense(expense.id)}
                                    className="text-red-500 hover:text-red-700 focus:outline-none"
                                    aria-label="Delete expense"
                                  >
                                    <TrashIcon className="h-5 w-5" />
                                  </button>
                                )}
                              </div>
                            </div>
                          </li>
                        );
                      }).filter(Boolean) /* Remove any null entries */}
                    </ul>
                  ) : (
                    <div className="text-center py-4 text-gray-500">
                      No expenses in this group yet
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8">
            <div className="sm:flex sm:items-center">
              <div className="sm:flex-auto">
                <h2 className="text-xl font-semibold text-gray-900">Settlements</h2>
                <p className="mt-2 text-sm text-gray-700">
                  Current settlements and suggested settlements for the group.
                </p>
              </div>
            </div>

            {balances && (
              <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Current Balances */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Current Balances</h3>
                  <div className="space-y-3">
                    {balances.balances.map((balance) => (
                      <div key={balance.user_id} className="flex justify-between items-center">
                        <span className="text-gray-900">{balance.user_name}</span>
                        <span className={`font-medium ${balance.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          ${Math.abs(balance.balance).toFixed(2)} {balance.balance >= 0 ? 'to receive' : 'to pay'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Suggested Settlements */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Suggested Settlements</h3>
                  {balances.suggested_settlements.length > 0 ? (
                    <div className="space-y-4">
                      {balances.suggested_settlements.map((settlement, index) => (
                        <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <p className="text-sm text-gray-900">
                              <span className="font-medium">{settlement.paid_by_name}</span> should pay{' '}
                              <span className="font-medium">{settlement.paid_to_name}</span>
                            </p>
                            <p className="text-lg font-semibold text-gray-900 mt-1">
                              ${settlement.amount.toFixed(2)}
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              setSelectedSettlement(settlement);
                              setShowSettleModal(true);
                            }}
                            className="ml-4 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            Settle
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-4">No settlements needed!</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {showExpenseModal && (
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
              <div className="bg-white rounded-lg max-w-md w-full p-6">
                <h2 className="text-lg font-medium mb-4">Add New Expense</h2>
                <form onSubmit={handleCreateExpense}>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                        Amount
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        name="amount"
                        id="amount"
                        required
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        value={newExpense.amount}
                        onChange={(e) => {
                          setNewExpense((prev) => ({ ...prev, amount: e.target.value }));
                          initializeExpenseSplits();
                        }}
                      />
                    </div>

                    <div>
                      <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                        Description
                      </label>
                      <input
                        type="text"
                        name="description"
                        id="description"
                        required
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        value={newExpense.description}
                        onChange={(e) =>
                          setNewExpense((prev) => ({ ...prev, description: e.target.value }))
                        }
                      />
                    </div>

                    <div>
                      <label htmlFor="paidById" className="block text-sm font-medium text-gray-700">
                        Paid By
                      </label>
                      <select
                        id="paidById"
                        name="paidById"
                        required
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                        value={newExpense.paidById}
                        onChange={(e) =>
                          setNewExpense((prev) => ({ ...prev, paidById: parseInt(e.target.value) }))
                        }
                      >
                        <option value="">Select who paid</option>
                        {group?.members.map((member) => (
                          <option key={member.id} value={member.id}>
                            {member.full_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Split Type
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        <button
                          type="button"
                          className={`px-3 py-2 text-sm font-medium rounded-md ${
                            splitType === 'equal'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                          onClick={() => {
                            setSplitType('equal');
                            initializeExpenseSplits();
                          }}
                        >
                          Split Equally
                        </button>
                        <button
                          type="button"
                          className={`px-3 py-2 text-sm font-medium rounded-md ${
                            splitType === 'percentage'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                          onClick={() => {
                            setSplitType('percentage');
                            initializeExpenseSplits();
                          }}
                        >
                          By Percentage
                        </button>
                        <button
                          type="button"
                          className={`px-3 py-2 text-sm font-medium rounded-md ${
                            splitType === 'custom'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                          onClick={() => {
                            setSplitType('custom');
                            initializeExpenseSplits();
                          }}
                        >
                          Custom Split
                        </button>
                      </div>
                    </div>

                    {newExpense.splits.length > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {splitType === 'percentage' ? 'Split Percentages' : 'Split Amounts'}
                        </label>
                        <div className="space-y-2">
                          {newExpense.splits.map((split, index) => {
                            const member = group?.members.find((m) => m.id === split.user_id);
                            return (
                              <div key={split.user_id} className="flex items-center gap-2">
                                <span className="text-sm text-gray-500 w-32 truncate">
                                  {member?.full_name}
                                </span>
                                <div className="flex-1 relative">
                                  <input
                                    type="number"
                                    step={splitType === 'percentage' ? '1' : '0.01'}
                                    min="0"
                                    max={splitType === 'percentage' ? '100' : undefined}
                                    required
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm pr-8"
                                    value={split.amount}
                                    onChange={(e) => {
                                      const newSplits = [...newExpense.splits];
                                      newSplits[index].amount = e.target.value;
                                      setNewExpense((prev) => ({ ...prev, splits: newSplits }));
                                    }}
                                  />
                                  {splitType === 'percentage' && (
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">
                                      %
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Receipt (optional)
                      </label>
                      <div className="mt-1 flex items-center">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleFileChange}
                          className="block w-full text-sm text-gray-500
                            file:mr-4 file:py-2 file:px-4
                            file:rounded-full file:border-0
                            file:text-sm file:font-semibold
                            file:bg-blue-50 file:text-blue-700
                            hover:file:bg-blue-100"
                        />
                        {selectedReceipt && (
                          <span className="ml-2 text-sm text-gray-500">
                            {selectedReceipt.name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3">
                    <button
                      type="button"
                      className="mt-3 sm:mt-0 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                      onClick={handleCloseExpenseModal}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                    >
                      Add Expense
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
          {/* Add Member Modal */}
          {showAddMemberModal && group && (
            <AddMemberModal
              isOpen={showAddMemberModal}
              onClose={() => setShowAddMemberModal(false)}
              onAddMember={handleAddMember}
              currentMembers={group.members}
            />
          )}
          {/* Settlement Confirmation Modal */}
          {showSettleModal && selectedSettlement && (
            <div className="fixed z-10 inset-0 overflow-y-auto">
              <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                  <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Confirm Settlement
                    </h3>
                    <p className="text-sm text-gray-500">
                      Are you sure you want to record this settlement?
                    </p>
                    <div className="mt-4 bg-gray-50 p-4 rounded-md">
                      <p className="text-sm text-gray-900">
                        <span className="font-medium">{selectedSettlement.paid_by_name}</span> will pay{' '}
                        <span className="font-medium">{selectedSettlement.paid_to_name}</span>
                      </p>
                      <p className="text-lg font-semibold text-gray-900 mt-1">
                        ${selectedSettlement.amount.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3">
                    <button
                      type="button"
                      onClick={() => setShowSettleModal(false)}
                      className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSettle}
                      className="mt-3 sm:mt-0 w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm"
                    >
                      Confirm Settlement
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
