export default function AssetHealthScore({ propertyId }) {
  const [score, setScore] = useState(null);
  useEffect(() => {
    fetch(`/api/asset-health/${propertyId}`).then(res => res.json()).then(setScore);
  }, []);
  return <div>Health Score: {score?.health_score}</div>;
}