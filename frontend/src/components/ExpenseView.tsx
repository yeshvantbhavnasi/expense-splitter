import React, { useState } from 'react';
import { Expense } from '../types';
import { expenseService } from '../api/services';
import { useAuth } from '../contexts/AuthContext';
import { formatCurrency } from '../utils/format';
import { DocumentArrowUpIcon, TrashIcon } from '@heroicons/react/24/outline';
import ReceiptModal from './ReceiptModal';

interface ExpenseViewProps {
  expense: Expense;
  groupId: string;
  onUpdate: (expense: Expense) => void;
  onDelete: () => void;
}

const ExpenseView: React.FC<ExpenseViewProps> = ({ 
  expense, 
  groupId, 
  onUpdate,
  onDelete 
}) => {
  const { user } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReceiptModal, setShowReceiptModal] = useState(false);

  const handleReceiptUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const updatedExpense = await expenseService.uploadReceipt(groupId, expense.id, file);
      onUpdate(updatedExpense);
    } catch (err) {
      setError('Failed to upload receipt');
      console.error('Receipt upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    try {
      await expenseService.deleteExpense(groupId, expense.id);
      onDelete();
    } catch (err) {
      setError('Failed to delete expense');
      console.error('Delete error:', err);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-4">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{expense.description}</h3>
          <p className="text-sm text-gray-500">
            Paid by {expense.paid_by_name} • {new Date(expense.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="text-xl font-semibold text-gray-900">
          {formatCurrency(expense.amount)}
        </div>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Split Details</h4>
        {expense.splits.map((split) => (
          <div key={split.user_id} className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">{split.user_name}</span>
            <span className="text-gray-900">{formatCurrency(split.amount)}</span>
          </div>
        ))}
      </div>

      {error && (
        <div className="mt-4 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="mt-6 flex justify-between items-center">
        <div className="flex space-x-4">
          {expense.receipt_url ? (
            <button
              onClick={() => setShowReceiptModal(true)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              View Receipt
            </button>
          ) : (
            <label className="relative cursor-pointer">
              <input
                type="file"
                className="hidden"
                accept="image/*,.pdf"
                onChange={handleReceiptUpload}
                disabled={uploading}
              />
              <span className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <DocumentArrowUpIcon className="h-5 w-5 mr-2" />
                {uploading ? 'Uploading...' : 'Upload Receipt'}
              </span>
            </label>
          )}
        </div>

        {expense.paid_by_id === user?.id && (
          <button
            onClick={handleDelete}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200"
          >
            <TrashIcon className="h-5 w-5 mr-2" />
            Delete
          </button>
        )}
      </div>

      {showReceiptModal && expense.receipt_url && (
        <ReceiptModal
          receiptUrl={expense.receipt_url}
          onClose={() => setShowReceiptModal(false)}
        />
      )}
    </div>
  );
};

export default ExpenseView;
