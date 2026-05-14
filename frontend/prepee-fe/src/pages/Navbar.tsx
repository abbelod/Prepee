import { useNavigate } from "react-router";
import { useAuth } from "./AuthProvider";
import api from "../services/api";

function Navbar() {
    const {user, loading, setUser} = useAuth();
    const navigate = useNavigate();
  

    const logoutUser = async () => {
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          // Call backend logout endpoint (adjust URL to your actual endpoint)
          await api.post('/auth/logout/', { refresh: refreshToken });
        }
      } catch (error) {
        console.error('Logout API call failed:', error);
        // Still proceed with frontend cleanup even if backend call fails
      } finally {
        // Clear all auth data from storage
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
  
        // Remove Authorization header from axios defaults
        delete api.defaults.headers.common['Authorization'];
  
        // Update React context (so UI updates immediately)
        setUser(null);
  
        // Redirect to login page
        navigate('/login');
      }

    }
    

    if (loading) return null; // optional: show spinner if you want
  
    return (
      <nav className="hidden items-center gap-6 text-sm font-medium text-slate-200 md:flex">
        <button onClick={() => navigate('/')} className="transition hover:text-white">
          Home
        </button>
        <button onClick={() => navigate('/leaderboard')} className="transition hover:text-white">
          Leaderboard
        </button>
        <button onClick={() => navigate('/about')} className="transition hover:text-white">
          About
        </button>
  
        <div className="flex items-center gap-2">
          {user ? (
            <>
              <span className="text-slate-100">Hi, {user.username}</span>
              <button 
                onClick={logoutUser}
                className="rounded-full border border-white/30 px-4 py-2 text-xs uppercase tracking-wide text-slate-100 transition hover:border-white hover:text-white"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <button 
                onClick={() => navigate('/login')}
                className="rounded-full border border-white/30 px-4 py-2 text-xs uppercase tracking-wide text-slate-100 transition hover:border-white hover:text-white"
              >
                Login
              </button>
              <button 
                onClick={() => navigate('/signup')}
                className="rounded-full bg-indigo-500 px-4 py-2 text-xs uppercase tracking-wide text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400"
              >
                Signup
              </button>
            </>
          )}
        </div>
      </nav>
    );
  }
  
  export default Navbar;
  