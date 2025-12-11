import { useState } from 'react';
import { useNavigate } from 'react-router';
import './App.css';

const quizCategories = [
  { title: 'Logical Reasoning', icon: '🧠' },
  { title: 'Biology', icon: '🧬' },
  { title: 'Mathematics', icon: '➗' },
  { title: 'English', icon: '📚' },
  { title: 'Chemistry', icon: '⚗️' },
  { title: 'Physics', icon: '🔭' },
  { title: 'ECAT', icon: '⚙️' },
  { title: 'MCAT', icon: '🏥' },
] as const;

const timeControls = ['5 min', '10 min', '15 min', 'ANY'] as const;

function HomePage() {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<(typeof quizCategories)[number]['title']>(quizCategories[0].title);
  const [selectedTime, setSelectedTime] = useState<(typeof timeControls)[number]>('10 min');
  const [isSearching, setIsSearching] = useState(false);


  const POLL_INTERVAL = 2000; // 2 seconds
  let pollingTimer: number;
  
  interface MatchResponse {
    status: "matched" | "waiting";
    match_id?: number;
    opponentName?: string;
    opponentCity?: string;
    questions?: any;
  }
  
  const handleStartMatch = async (): Promise<void> => {
    setIsSearching(true);
  
    const token = localStorage.getItem("accessToken");
    if (!token) {
      console.error("No access token found");
      setIsSearching(false);
      return;
    }
  
    const poll = async () => {
      try {
        const response = await fetch("http://localhost:8000/matchmaking/find/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            category: selectedCategory,
            timeControl: selectedTime,
          }),
        });
  
        if (!response.ok) {
          console.error("Failed to check match", response.statusText);
          setIsSearching(false);
          if (pollingTimer) clearInterval(pollingTimer);
          return;
        }
  
        const data: MatchResponse = await response.json();
        console.log("Polling response:", data);
  
        if (data.status === "matched" && data.match_id) {
          if (pollingTimer) clearInterval(pollingTimer);
  
          navigate("/quiz", {
            state: {
              matchId: data.match_id,
              opponentName: data.opponentName,
              opponentCity: data.opponentCity,
              questions: data.questions,
              timeControl: selectedTime,
            },
          });
        } else {
          console.log("Still waiting...");
        }
      } catch (error) {
        console.error("Error during polling:", error);
        setIsSearching(false);
        if (pollingTimer) clearInterval(pollingTimer);
      }
    };
  
    // Start immediately
    poll();
    pollingTimer = setInterval(poll, POLL_INTERVAL);
  };

  
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Loading Overlay */}
      {isSearching && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4">
            {/* Spinning Circle */}
            <div className="h-16 w-16 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
            <p className="text-lg font-medium text-white">Finding a match...</p>
          </div>
        </div>
      )}

      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-2xl text-indigo-300">
              ⚡
            </span>
            Prepee Quiz
          </div>
          <nav className="hidden items-center gap-6 text-sm font-medium text-slate-200 md:flex">
            <button 
              onClick={() => navigate('/')}
              className="transition hover:text-white"
            >
              Home
            </button>
            <button 
              onClick={() => navigate('/leaderboard')}
              className="transition hover:text-white"
            >
              Leaderboard
            </button>
            <button 
              onClick={() => navigate('/about')}
              className="transition hover:text-white"
            >
              About
            </button>
            <div className="flex items-center gap-2">
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
            </div>
          </nav>
          <button className="md:hidden" aria-label="Open Menu">
            <span className="inline-block h-5 w-6 border-y border-white/70" />
          </button>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-12 px-4 py-12 sm:py-16">
        <section className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-indigo-300">
            Ready, Set, Quiz
          </p>
          <h1 className="mt-4 text-4xl font-bold leading-tight text-white md:text-5xl">
            Smart Entry Test Preparation
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base text-slate-300 md:text-lg">
            Pick a category, set your time control, and jump into a head-to-head knowledge match.
            Every game is a chance to sharpen your thinking muscles.
          </p>
          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <div className="w-full max-w-xs">
              <label className="block text-left text-sm font-medium text-slate-300">
                Time Control
              </label>
              <div className="relative mt-2">
                <select
                  value={selectedTime}
                  onChange={(event) => setSelectedTime(event.target.value as (typeof timeControls)[number])}
                  className="w-full rounded-2xl border-none bg-white/5 px-4 py-3 pr-10 text-sm text-white ring-1 ring-white/20 transition focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {timeControls.map((option) => (
                    <option className="bg-slate-900 text-white" key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-300">
                  ▾
                </span>
              </div>
            </div>
            <button 
              className="w-full max-w-xs rounded-2xl bg-indigo-500 px-6 py-3 text-sm font-semibold uppercase tracking-wide text-white shadow-xl shadow-indigo-500/30 transition hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleStartMatch}
              disabled={isSearching}
            >
              Start Match
            </button>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-white">Choose a category</h2>
            <span className="text-sm text-slate-400">Selected: {selectedCategory}</span>
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {quizCategories.map((category) => (
              <button
                key={category.title}
                onClick={() => setSelectedCategory(category.title)}
                aria-pressed={selectedCategory === category.title}
                className={`rounded-3xl border border-white/10 bg-white/5 p-6 text-left transition hover:-translate-y-1 hover:border-indigo-400 hover:bg-white/10 hover:shadow-indigo-500/30 ${
                  selectedCategory === category.title ? 'ring-2 ring-indigo-400' : 'ring-0'
                }`}
              >
                <div className="flex items-center gap-4">
                  <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/20 text-2xl">
                    {category.icon}
                  </span>
                  <div>
                    <p className="text-lg font-semibold text-white">{category.title}</p>
                    <p className="text-sm text-slate-400">20 curated questions</p>
                  </div>
                </div>
                <p className="mt-4 text-sm text-slate-300">
                  Sharpen your understanding with quick matches tailored for focused practice.
                </p>
              </button>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-slate-950/80">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} PrePee Quiz. All rights reserved.</p>
          <div className="flex flex-wrap gap-4">
            <a className="transition hover:text-white" href="#">
              Privacy
            </a>
            <a className="transition hover:text-white" href="#">
              Terms
            </a>
            <a className="transition hover:text-white" href="#">
              Support
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default HomePage;
