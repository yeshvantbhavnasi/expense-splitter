import React, { useState, useEffect } from 'react';
import { 
  Modal, 
  ModalOverlay, 
  ModalContent, 
  ModalHeader, 
  ModalCloseButton, 
  ModalBody, 
  VStack, 
  Text, 
  Image, 
  Button, 
  HStack, 
  useToast 
} from '@chakra-ui/react';
import { Expense } from '../types';
import { expenseService } from '../api/services';

interface ExpenseDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  groupId: number;
  expenseId: number;
}

export const ExpenseDetailModal: React.FC<ExpenseDetailModalProps> = ({ 
  isOpen, 
  onClose, 
  groupId, 
  expenseId 
}) => {
  const [expense, setExpense] = useState<Expense | null>(null);
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const toast = useToast();

  useEffect(() => {
    if (isOpen && groupId && expenseId) {
      fetchExpenseDetails();
    }
  }, [isOpen, groupId, expenseId]);

  const fetchExpenseDetails = async () => {
    try {
      const details = await expenseService.getExpenseDetails(groupId, expenseId);
      setExpense(details);
    } catch (error) {
      toast({
        title: "Error fetching expense details",
        status: "error",
        duration: 3000,
        isClosable: true
      });
    }
  };

  const handleReceiptUpload = async () => {
    if (!receiptFile) return;

    try {
      const result = await expenseService.uploadReceipt(expenseId, receiptFile);
      // Update the expense with the new receipt URL
      setExpense(prev => prev ? { ...prev, receipt_url: result.receipt_url } : null);
      
      toast({
        title: "Receipt uploaded successfully",
        status: "success",
        duration: 3000,
        isClosable: true
      });
    } catch (error) {
      toast({
        title: "Error uploading receipt",
        status: "error",
        duration: 3000,
        isClosable: true
      });
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        toast({
          title: "File too large",
          description: "Maximum file size is 5MB",
          status: "error",
          duration: 3000,
          isClosable: true
        });
        return;
      }
      setReceiptFile(file);
    }
  };

  if (!expense) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Expense Details</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Text><strong>Description:</strong> {expense.description}</Text>
            <Text><strong>Amount:</strong> ${expense.amount.toFixed(2)}</Text>
            <Text><strong>Date:</strong> {new Date(expense.date).toLocaleDateString()}</Text>
            <Text><strong>Paid By:</strong> {expense.paid_by_id}</Text>

            {/* Receipt Section */}
            {expense.receipt_url && (
              <Image 
                src={`http://localhost:8000${expense.receipt_url}`} 
                alt="Expense Receipt" 
                maxH="300px" 
                objectFit="cover" 
              />
            )}

            {/* Receipt Upload */}
            <HStack>
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileChange} 
              />
              {receiptFile && (
                <Button 
                  colorScheme="blue" 
                  onClick={handleReceiptUpload}
                >
                  Upload Receipt
                </Button>
              )}
            </HStack>

            {/* Expense Splits */}
            <Text><strong>Splits:</strong></Text>
            {expense.splits.map((split, index) => (
              <HStack key={index} justifyContent="space-between">
                <Text>{`User ${split.user_id}`}</Text>
                <Text>${split.amount.toFixed(2)}</Text>
              </HStack>
            ))}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
