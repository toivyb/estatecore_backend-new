import { loadStripe } from '@stripe/stripe-js';

// Stripe Configuration
const STRIPE_PUBLISHABLE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || 
  'pk_test_51RtgzlBqa0QakynAVXMBBFG8Q1z0gB2XpyLpj4qRYxpJd1ROxbRvaPr6oRHNegeWFOFPPTxN6Kt3J7steyN6INzj00000000'; // Mock test key for demo

// Initialize Stripe
let stripePromise;
const getStripe = () => {
  if (!stripePromise) {
    stripePromise = loadStripe(STRIPE_PUBLISHABLE_KEY);
  }
  return stripePromise;
};

export default getStripe;

// Export configuration for components
export const stripeConfig = {
  appearance: {
    theme: 'stripe',
    variables: {
      colorPrimary: '#2563eb',
      colorBackground: '#ffffff',
      colorText: '#1f2937',
      colorDanger: '#ef4444',
      fontFamily: 'Inter, system-ui, sans-serif',
      spacingUnit: '4px',
      borderRadius: '8px',
    },
  },
  clientSecret: null, // Will be set when creating payment intent
};

// Payment amount helpers
export const formatCurrency = (amount, currency = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount / 100); // Stripe amounts are in cents
};

export const convertToCents = (dollarAmount) => {
  return Math.round(dollarAmount * 100);
};