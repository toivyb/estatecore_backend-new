import AccessLog from "./AccessLog";
import GateControl from "./GateControl";
import VisitorPassManager from "./VisitorPassManager";
import GeofenceUnlock from "./GeofenceUnlock";

export default function AccessControl() {
  return <div>
    <h2 className="text-xl font-bold">Access Control</h2>
    <GateControl propertyId={1} gateList={[{id:1, name:"Main Gate"}]} />
    <VisitorPassManager propertyId={1} />
    <GeofenceUnlock />
    <AccessLog propertyId={1} />
  </div>;
}