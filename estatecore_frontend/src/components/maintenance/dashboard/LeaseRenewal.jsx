export default function LeaseRenewal({ onTime, goodTenant }) {
  const handleSuggest = async () => {
    const res = await fetch('/api/lease-renewal-suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ on_time_rent: onTime, good_tenant: goodTenant })
    });
    const data = await res.json();
    alert(`Suggest ${data.suggested_months} months with $${data.suggested_rent_increase} increase`);
  };
  return <button onClick={handleSuggest}>Suggest Renewal</button>;
}