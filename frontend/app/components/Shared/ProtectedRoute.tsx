
import { useAuth } from '../../components/Auth/AuthConext';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  return user ? <>{children}</> : null; 
};

export default ProtectedRoute;