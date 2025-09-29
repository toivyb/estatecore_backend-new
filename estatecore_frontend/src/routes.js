import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import RentPage from "./pages/RentPage";
import Maintenance from "./pages/Maintenance";
import AccessLog from "./pages/AccessLog";
import Invite from "./pages/Invite";
import VideoInspection from "./pages/VideoInspection";
import Users from "./pages/Users";
import CollaborationDashboard from "./pages/CollaborationDashboard";
import VideoConferencing from "./components/VideoConferencing";

export default [
  { path: "/login", element: <Login /> },
  { path: "/dashboard", element: <Dashboard /> },
  { path: "/rent", element: <RentPage /> },
  { path: "/maintenance", element: <Maintenance /> },
  { path: "/access-log", element: <AccessLog /> },
  { path: "/invite", element: <Invite /> },
  { path: "/video-inspection", element: <VideoInspection /> },
  { path: "/users", element: <Users /> },
  { path: "/collaboration", element: <CollaborationDashboard /> },
  { path: "/meeting/:meetingId", element: <VideoConferencing /> }
];
