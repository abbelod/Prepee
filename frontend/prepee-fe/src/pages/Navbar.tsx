import { useContext } from "react";
import { useNavigate } from "react-router";
import { AuthContext } from "./AuthProvider";


function Navbar() {
    const { user, loading } = useContext(AuthContext);
    const navigate = useNavigate();
  
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
                onClick={() => {
                  // clear token and update auth state
                  localStorage.removeItem("accessToken");
                  localStorage.removeItem("refreshToken");
                  window.location.reload(); // simple way to update UI
                }}
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
  