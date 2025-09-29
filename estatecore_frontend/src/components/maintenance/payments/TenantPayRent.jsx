import React, { useState } from "react";
import axios from "axios";
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe("pk_test_..."); // replace with your Stripe publishable key

export default function TenantPayRent({ rentId, tenantId, amount, onPaid }) {
  const [clientSecret, setClientSecret] = useState("");

  const createPayment = async () => {
    const res = await axios.post("/api/payments/create", {
      rent_id: rentId,
      tenant_id: tenantId,
      amount: amount,
    });
    setClientSecret(res.data.client_secret);
    // Stripe integration
    const stripe = await stripePromise;
    const { error } = await stripe.redirectToCheckout({
      sessionId: res.data.client_secret,
    });
    if (error) {
      alert(error.message);
    }
    if (onPaid) onPaid();
  };

  return (
    <div>
      <button className="bg-green-600 text-white px-4 py-2 rounded" onClick={createPayment}>
        Pay Now (${amount})
      </button>
    </div>
  );
}
