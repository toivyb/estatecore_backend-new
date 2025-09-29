import PDFReportButton from "./PDFReportButton";
import CashFlowWidget from "./CashFlowWidget";
export default function RentManagement() {
  return <div>
    <h2 className="text-xl font-bold">Rent Management</h2>
    <PDFReportButton />
    <CashFlowWidget propertyId={1} />
  </div>;
}