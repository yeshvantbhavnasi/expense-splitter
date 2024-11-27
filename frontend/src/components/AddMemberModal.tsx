import { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { User } from '../types';
import { userService } from '../api/services';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface AddMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddMember: (userId: number) => Promise<void>;
  currentMembers: User[];
}

export default function AddMemberModal({
  isOpen,
  onClose,
  onAddMember,
  currentMembers,
}: AddMemberModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const searchUsers = async () => {
      if (!searchQuery.trim()) {
        setSearchResults([]);
        return;
      }

      try {
        setLoading(true);
        const users = await userService.searchUsers(searchQuery);
        // Filter out current members
        const filteredUsers = users.filter(
          (user) => !currentMembers.some((member) => member.id === user.id)
        );
        setSearchResults(filteredUsers);
      } catch (err) {
        setError('Failed to search users');
      } finally {
        setLoading(false);
      }
    };

    const debounceTimeout = setTimeout(searchUsers, 300);
    return () => clearTimeout(debounceTimeout);
  }, [searchQuery, currentMembers]);

  const handleAddMember = async (userId: number) => {
    try {
      await onAddMember(userId);
      onClose();
    } catch (err) {
      setError('Failed to add member');
    }
  };

  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      className="relative z-50"
    >
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="relative bg-white rounded-lg w-full max-w-md p-6">
          <div className="absolute top-4 right-4">
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <Dialog.Title className="text-lg font-medium mb-4">
            Add Member to Group
          </Dialog.Title>

          <div className="mb-4">
            <input
              type="text"
              placeholder="Search users by name or email"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {error && (
            <div className="mb-4 text-red-500 text-sm">{error}</div>
          )}

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {loading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
              </div>
            ) : searchResults.length > 0 ? (
              searchResults.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-md"
                >
                  <div>
                    <div className="font-medium">{user.full_name}</div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </div>
                  <button
                    onClick={() => handleAddMember(user.id)}
                    className="ml-4 px-3 py-1 bg-blue-500 text-white text-sm font-medium rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Add
                  </button>
                </div>
              ))
            ) : searchQuery ? (
              <div className="text-center py-4 text-gray-500">No users found</div>
            ) : null}
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
}
