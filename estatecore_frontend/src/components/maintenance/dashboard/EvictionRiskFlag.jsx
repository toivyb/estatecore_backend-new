export default function EvictionRiskFlag({ tenantId }) {
  const [risk, setRisk] = useState(null);
  useEffect(() => {
    fetch(`/api/eviction-risk/${tenantId}`).then(res => res.json()).then(setRisk);
  }, []);
  return <div>Eviction Risk: {risk?.risk} ({risk?.score})</div>;
}