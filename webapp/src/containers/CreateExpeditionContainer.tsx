import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useExpeditions } from '@/hooks/useExpeditions';
import { useExpeditionWizard } from '@/hooks/useExpeditionWizard';
import { useExpeditionValidation } from '@/utils/validation/expeditionValidation';
import { CreateExpeditionPresenter } from '@/components/expedition/CreateExpeditionPresenter';
import { SimpleExpeditionForm } from '@/components/expedition/SimpleExpeditionForm';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';
import { productService } from '@/services/api/productService';
import { hapticFeedback, showAlert } from '@/utils/telegram';
import {
  CreateExpeditionRequest,
  CreateExpeditionItemRequest,
  QualityGrade,
  Product,
} from '@/types/expedition';

interface SelectedProductItem {
  product_id: number;
  product: Product;
  quantity: number;
  quality_grade: QualityGrade;
  unit_price: number;
}

interface CreateExpeditionState {
  name: string;
  selectedProducts: SelectedProductItem[];
}

const TOTAL_STEPS = 4;
const USE_SIMPLE_FORM = true; // Toggle between simple form and wizard

/**
 * Container component for CreateExpedition
 * Handles state management, data fetching, and business logic
 */
export const CreateExpeditionContainer: React.FC = () => {
  const navigate = useNavigate();
  const { createExpedition } = useExpeditions();

  // State
  const [loading, setLoading] = useState(false);
  const [availableProducts, setAvailableProducts] = useState<Product[]>([]);
  const [expeditionData, setExpeditionData] = useState<CreateExpeditionState>({
    name: '',
    selectedProducts: [],
  });

  // Hooks
  const wizard = useExpeditionWizard({
    totalSteps: TOTAL_STEPS,
  });

  const validation = useExpeditionValidation(
    {
      name: expeditionData.name,
      selectedProducts: expeditionData.selectedProducts,
    },
    wizard.currentStep
  );

  // Load products on mount
  useEffect(() => {
    const loadProducts = async () => {
      try {
        const products = await productService.getAll();
        setAvailableProducts(products);
      } catch (error) {
        console.error('Failed to load products:', error);
        setAvailableProducts([]);
        showAlert('Failed to load products. Please check your connection and try again.');
      }
    };

    loadProducts();
  }, []);

  // Step validation
  const isStepValid = useCallback((step: number): boolean => {
    return validation.isStepValid(step);
  }, [validation]);

  // Event handlers
  const handleNameChange = useCallback((name: string) => {
    setExpeditionData(prev => ({ ...prev, name }));
  }, []);

  const handleProductToggle = useCallback((product: Product) => {
    hapticFeedback('light');
    setExpeditionData(prev => {
      const isSelected = prev.selectedProducts.some(p => p.product_id === product.id);

      if (isSelected) {
        return {
          ...prev,
          selectedProducts: prev.selectedProducts.filter(p => p.product_id !== product.id),
        };
      } else {
        return {
          ...prev,
          selectedProducts: [
            ...prev.selectedProducts,
            {
              product_id: product.id,
              product,
              quantity: 1,
              quality_grade: 'B' as QualityGrade,
              unit_price: product.price,
            },
          ],
        };
      }
    });
  }, []);

  const handleQuantityChange = useCallback((productId: number, quantity: number) => {
    setExpeditionData(prev => ({
      ...prev,
      selectedProducts: prev.selectedProducts.map(item =>
        item.product_id === productId ? { ...item, quantity } : item
      ),
    }));
  }, []);

  const handleQualityChange = useCallback((productId: number, quality_grade: QualityGrade) => {
    setExpeditionData(prev => ({
      ...prev,
      selectedProducts: prev.selectedProducts.map(item =>
        item.product_id === productId ? { ...item, quality_grade } : item
      ),
    }));
  }, []);

  const handlePriceChange = useCallback((productId: number, unit_price: number) => {
    setExpeditionData(prev => ({
      ...prev,
      selectedProducts: prev.selectedProducts.map(item =>
        item.product_id === productId ? { ...item, unit_price } : item
      ),
    }));
  }, []);

  const handleNext = useCallback(() => {
    if (isStepValid(wizard.currentStep)) {
      wizard.goToNextStep();
    }
  }, [wizard, isStepValid]);

  const handlePrevious = useCallback(() => {
    wizard.goToPreviousStep();
  }, [wizard]);

  const handleStepClick = useCallback((step: number) => {
    wizard.goToStep(step);
  }, [wizard]);

  const handleSubmit = useCallback(async () => {
    try {
      setLoading(true);
      hapticFeedback('success');

      // Create expedition with only name (description and deadline can be added later)
      const expeditionRequest: CreateExpeditionRequest = {
        name: expeditionData.name,
      };

      const newExpedition = await createExpedition(expeditionRequest);

      if (newExpedition) {
        // Add items to expedition (only in wizard mode)
        if (!USE_SIMPLE_FORM && expeditionData.selectedProducts.length > 0) {
          const itemsRequest: CreateExpeditionItemRequest = {
            items: expeditionData.selectedProducts.map(item => ({
              product_id: item.product_id,
              quantity: item.quantity,
              quality_grade: item.quality_grade,
            })),
          };

          await expeditionItemsService.addItems(newExpedition.id, itemsRequest);
        }

        // Navigate to expedition details
        navigate(`/expedition/${newExpedition.id}`);
      }
    } catch (error) {
      console.error('Error creating expedition:', error);
      hapticFeedback('error');
      showAlert('Failed to create expedition. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [expeditionData, createExpedition, navigate]);

  const handleCancel = useCallback(() => {
    navigate('/');
  }, [navigate]);

  // Render simple form or wizard based on configuration
  if (USE_SIMPLE_FORM) {
    return (
      <SimpleExpeditionForm
        name={expeditionData.name}
        onNameChange={handleNameChange}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        loading={loading}
      />
    );
  }

  return (
    <CreateExpeditionPresenter
      // Wizard state
      currentStep={wizard.currentStep}
      isFirstStep={wizard.isFirstStep}
      isLastStep={wizard.isLastStep}
      totalSteps={TOTAL_STEPS}
      // Expedition data
      name={expeditionData.name}
      selectedProducts={expeditionData.selectedProducts}
      availableProducts={availableProducts}
      // Loading state
      loading={loading}
      // Validation
      isStepValid={isStepValid(wizard.currentStep)}
      canNavigateToStep={wizard.canNavigateToStep}
      // Event handlers
      onNameChange={handleNameChange}
      onProductToggle={handleProductToggle}
      onQuantityChange={handleQuantityChange}
      onQualityChange={handleQualityChange}
      onPriceChange={handlePriceChange}
      onNext={handleNext}
      onPrevious={handlePrevious}
      onStepClick={handleStepClick}
      onSubmit={handleSubmit}
    />
  );
};
