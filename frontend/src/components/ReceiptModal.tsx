import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ReceiptModalProps {
  receiptUrl: string;
  onClose: () => void;
}

const ReceiptModal: React.FC<ReceiptModalProps> = ({ receiptUrl, onClose }) => {
  const isPDF = receiptUrl.toLowerCase().endsWith('.pdf');

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex justify-between items-start">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Receipt
              </h3>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            <div className="mt-2 max-h-[70vh] overflow-auto">
              {isPDF ? (
                <iframe
                  src={receiptUrl}
                  className="w-full h-[70vh]"
                  title="Receipt PDF"
                />
              ) : (
                <img
                  src={receiptUrl}
                  alt="Receipt"
                  className="max-w-full h-auto"
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReceiptModal;
