import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { Loader2 } from 'lucide-react';

const Login = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary via-secondary to-primary">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary-foreground mx-auto" />
          <p className="text-primary-foreground">Carregando...</p>
        </div>
      </div>
    );
  }

  return <LoginForm />;
};

export default Login;
