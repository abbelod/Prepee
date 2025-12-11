import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router';

type LeaderboardEntry = {
  username: string;
  position: number;
  city: string;
  elo: number;
};

const medalStyles: Record<number, string> = {
  1: 'border-amber-400/60 bg-gradient-to-r from-amber-500/20 to-amber-300/10 shadow-lg shadow-amber-500/20',
  2: 'border-slate-300/50 bg-gradient-to-r from-slate-300/15 to-slate-100/5 shadow-lg shadow-slate-300/10',
  3: 'border-orange-400/50 bg-gradient-to-r from-orange-500/15 to-orange-400/5 shadow-lg shadow-orange-500/10',
};

function LeaderboardPage() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    let isMounted = true;

    const fetchLeaderboard = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('http://127.0.0.1:8000/api/leaderboards');
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        const data: LeaderboardEntry[] = await response.json();
        if (isMounted) {
          setEntries(data);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load leaderboard', err);
          setError('Unable to load the leaderboard right now. Please try again.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchLeaderboard();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredEntries = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return entries;
    return entries.filter((entry) =>
      [entry.username, entry.city].some((value) => value.toLowerCase().includes(term))
    );
  }, [entries, query]);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-lg font-semibold tracking-tight text-white transition hover:text-indigo-300"
          >
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-2xl text-indigo-300">
              ⚡
            </span>
            Prepee Leaderboard
          </button>
          <div className="flex items-center gap-3 text-sm font-medium text-slate-200">
            <button
              onClick={() => navigate('/')}
              className="rounded-full border border-white/20 px-4 py-2 transition hover:border-white hover:text-white"
            >
              Home
            </button>
            <button
              onClick={() => navigate('/quiz')}
              className="rounded-full bg-indigo-500 px-4 py-2 text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400"
            >
              Play Now
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-10 sm:py-12">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.25em] text-indigo-300">
              Global Standings
            </p>
            <h1 className="mt-2 text-3xl font-bold leading-tight text-white sm:text-4xl">
              Leaderboard
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-300 sm:text-base">
              Track the top performers and see where you rank. Search by username or city to
              find friends and rivals.
            </p>
          </div>
          <div className="flex w-full max-w-sm items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 ring-1 ring-white/10 focus-within:ring-2 focus-within:ring-indigo-500">
            <span className="text-slate-400">🔍</span>
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by username or city"
              className="w-full bg-transparent text-sm text-white placeholder:text-slate-500 outline-none"
            />
          </div>
        </div>

        <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl shadow-indigo-500/10 backdrop-blur">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <h2 className="text-lg font-semibold text-white">Top players</h2>
            {loading ? (
              <span className="text-xs uppercase tracking-wide text-slate-400">Loading...</span>
            ) : (
              <span className="text-xs uppercase tracking-wide text-slate-400">
                {filteredEntries.length} players
              </span>
            )}
          </div>

          {error && (
            <div className="border-b border-white/10 bg-red-500/10 px-6 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          <div className="max-h-[70vh] overflow-auto">
            <table className="min-w-full divide-y divide-white/10">
              <thead className="bg-white/5 text-left text-xs uppercase tracking-wide text-slate-300 backdrop-blur">
                <tr>
                  <th className="px-6 py-3">Position</th>
                  <th className="px-6 py-3">Username</th>
                  <th className="px-6 py-3">City</th>
                  <th className="px-6 py-3 text-right">ELO</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 text-sm">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-slate-400">
                      Fetching leaderboard...
                    </td>
                  </tr>
                ) : filteredEntries.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-slate-400">
                      No players found.
                    </td>
                  </tr>
                ) : (
                  filteredEntries.map((entry) => {
                    const medalClass = medalStyles[entry.position] ?? 'border-transparent';
                    return (
                      <tr
                        key={entry.username}
                        className={`transition hover:bg-white/5 ${entry.position <= 3 ? medalClass : ''}`}
                      >
                        <td className="px-6 py-4 font-semibold text-slate-100">
                          <span
                            className={`inline-flex h-9 w-9 items-center justify-center rounded-full text-base ${
                              entry.position === 1
                                ? 'bg-amber-500/20 text-amber-200 ring-1 ring-amber-300/60'
                                : entry.position === 2
                                  ? 'bg-slate-300/20 text-slate-100 ring-1 ring-slate-200/60'
                                  : entry.position === 3
                                    ? 'bg-orange-500/20 text-orange-200 ring-1 ring-orange-300/60'
                                    : 'bg-white/10 text-white ring-1 ring-white/10'
                            }`}
                          >
                            {entry.position}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-medium text-white">{entry.username}</td>
                        <td className="px-6 py-4 text-slate-300">{entry.city}</td>
                        <td className="px-6 py-4 text-right font-semibold text-indigo-100">
                          {entry.elo.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

export default LeaderboardPage;

