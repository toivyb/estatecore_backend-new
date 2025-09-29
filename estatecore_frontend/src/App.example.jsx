import { HashRouter } from 'react-router-dom';
import AdminRoutes from './routes/AdminRoutes';

export default function App(){
  return (
    <HashRouter>
      <AdminRoutes />
    </HashRouter>
  );
}
