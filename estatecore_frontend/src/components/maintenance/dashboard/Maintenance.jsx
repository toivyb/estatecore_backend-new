import VideoInspection from "./VideoInspection";
import IncidentReport from "./IncidentReport";
export default function Maintenance() {
  return <div>
    <h2 className="text-xl font-bold">Maintenance</h2>
    <VideoInspection propertyId={1} />
    <IncidentReport propertyId={1} />
  </div>;
}