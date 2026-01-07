import Navbar from "./Navbar";
function AboutPage() {
  const features = [
    {
      title: '1v1 Quiz Matches',
      description: 'Challenge other students in real-time head-to-head quiz battles.',
      icon: '⚔️',
    },
    {
      title: 'Time-Controlled Quizzes',
      description: 'Choose from 5, 10, or 15-minute time controls to match your pace.',
      icon: '⏱️',
    },
    {
      title: 'Topic-Based Categories',
      description: 'Practice Math, Physics, Biology, English, Chemistry, and Logical Reasoning.',
      icon: '📚',
    },
    {
      title: 'ELO-Based Matchmaking',
      description: 'Get matched with players of similar skill level for fair competition.',
      icon: '🎯',
    },
    {
      title: 'Modern UI/UX',
      description: 'Enjoy a clean, intuitive interface designed for seamless learning.',
      icon: '✨',
    },
    {
      title: 'Real-Time Results',
      description: 'See your performance instantly with detailed analytics and feedback.',
      icon: '📊',
    },
  ];

  const teamMembers = [
    {
      name: 'Alex Johnson',
      role: 'Lead Developer',
      avatar: '👨‍💻',
    },
    {
      name: 'Sarah Chen',
      role: 'UI/UX Designer',
      avatar: '👩‍🎨',
    },
    {
      name: 'Michael Park',
      role: 'Backend Engineer',
      avatar: '👨‍🔧',
    },
    {
      name: 'Emily Davis',
      role: 'Product Manager',
      avatar: '👩‍💼',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-2xl text-indigo-300">
              ⚡
            </span>
            PrePee Quiz
          </div>
          {/* <nav className="hidden items-center gap-6 text-sm font-medium text-slate-200 md:flex">
            <a className="transition hover:text-white" href="#">
              Home
            </a>
            <a className="transition hover:text-white" href="#">
              Leaderboard
            </a>
            <a className="text-indigo-400 transition hover:text-indigo-300" href="#">
              About
            </a>
            <div className="flex items-center gap-2">
              <button className="rounded-full border border-white/30 px-4 py-2 text-xs uppercase tracking-wide text-slate-100 transition hover:border-white hover:text-white">
                Login
              </button>
              <button className="rounded-full bg-indigo-500 px-4 py-2 text-xs uppercase tracking-wide text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400">
                Signup
              </button>
            </div>
          </nav> */}
          <Navbar>

          </Navbar>
          <button className="md:hidden" aria-label="Open Menu">
            <span className="inline-block h-5 w-6 border-y border-white/70" />
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-12 sm:py-16">
        {/* Hero Section */}
        <section className="mb-20 text-center">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-indigo-300">
            Our Story
          </p>
          <h1 className="mt-4 text-4xl font-bold leading-tight text-white md:text-6xl">
            About Prepee
          </h1>
          <p className="mx-auto mt-6 max-w-3xl text-lg text-slate-300 md:text-xl">
            A modern quiz platform where students prepare through fast-paced MCQ matches. Challenge
            yourself, compete with peers, and master entry test concepts in an engaging, competitive
            environment.
          </p>
        </section>

        {/* Mission Section */}
        <section className="mb-20">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 p-8 md:p-12">
            <h2 className="mb-6 text-3xl font-bold text-white md:text-4xl">Our Mission</h2>
            <div className="space-y-4 text-base leading-relaxed text-slate-300 md:text-lg">
              <p>
                At Prepee, we're dedicated to helping students excel in their entry test
                preparations—whether for Engineering, Medical, Computer Science, or other competitive
                fields. We believe that preparation should be engaging, efficient, and effective.
              </p>
              <p>
                Our platform focuses on improving problem-solving speed through time-controlled
                quizzes, ensuring you're not just knowledgeable but also quick under pressure—a
                critical skill for any competitive exam.
              </p>
              <p>
                We provide fair competitive learning through intelligent matchmaking and
                time-control features, matching you with peers of similar skill levels so every
                match is a meaningful learning experience.
              </p>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="mb-20">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">Key Features</h2>
            <p className="mt-4 text-slate-400">
              Everything you need to prepare effectively and compete fairly
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group rounded-3xl border border-white/10 bg-white/5 p-6 transition hover:-translate-y-1 hover:border-indigo-400 hover:bg-white/10 hover:shadow-xl hover:shadow-indigo-500/20"
              >
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/20 text-3xl transition group-hover:scale-110">
                  {feature.icon}
                </div>
                <h3 className="mb-2 text-xl font-semibold text-white">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Team Section */}
        <section className="mb-20">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-white md:text-4xl">Meet the Team</h2>
            <p className="mt-4 text-slate-400">The passionate people behind Prepee</p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {teamMembers.map((member, index) => (
              <div
                key={index}
                className="group rounded-3xl border border-white/10 bg-white/5 p-6 text-center transition hover:-translate-y-1 hover:border-indigo-400 hover:bg-white/10 hover:shadow-xl hover:shadow-indigo-500/20"
              >
                <div className="mb-4 flex justify-center">
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-indigo-500/20 text-4xl transition group-hover:scale-110">
                    {member.avatar}
                  </div>
                </div>
                <h3 className="mb-1 text-lg font-semibold text-white">{member.name}</h3>
                <p className="text-sm text-indigo-400">{member.role}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Call to Action Section */}
        <section className="mb-12">
          <div className="rounded-3xl border border-indigo-500/30 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 p-8 text-center shadow-2xl shadow-indigo-500/20 md:p-12">
            <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
              Ready to Start Practicing?
            </h2>
            <p className="mx-auto mb-8 max-w-2xl text-lg text-slate-300">
              Join thousands of students preparing for their entry tests. Challenge yourself, track
              your progress, and climb the leaderboard.
            </p>
            <button className="rounded-2xl bg-indigo-500 px-8 py-4 text-base font-semibold uppercase tracking-wide text-white shadow-xl shadow-indigo-500/30 transition hover:bg-indigo-400 hover:shadow-2xl hover:shadow-indigo-500/40">
              Start Practicing
            </button>
          </div>
        </section>
      </main>

      {/* Footer */}
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

export default AboutPage;

