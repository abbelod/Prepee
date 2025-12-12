import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router';

const quizQuestions = [
  {
    id: 1,
    category: 'Logical Reasoning',
    question: 'If A is 25% faster than B, how much slower is B compared to A?',
    options: ['20% slower', '25% slower', '30% slower', '15% slower'],
  },
  {
    id: 2,
    category: 'Physics',
    question: 'Which law explains the relationship between voltage, current, and resistance?',
    options: ['Ohm’s Law', 'Newton’s Law', 'Hooke’s Law', 'Faraday’s Law'],
  },
  {
    id: 3,
    category: 'Biology',
    question: 'What structure controls the exchange of materials between the nucleus and cytoplasm?',
    options: ['Golgi apparatus', 'Nuclear membrane', 'Ribosome', 'Lysosome'],
  },
];

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0');
  const secs = Math.floor(seconds % 60)
    .toString()
    .padStart(2, '0');
  return `${mins}:${secs}`;
};

export default function QuizPage() {
  const location = useLocation();
  const matchData = (location.state || null) as {
    matchId?: number;
    opponentName?: string;
    opponentCity?: string;
    timeControl?: string;
    questions?: typeof quizQuestions;
  } | null;

  // Derive starting time in seconds from timeControl if provided (e.g., "10 min")
  const initialTimeSeconds = useMemo(() => {
    const raw = matchData?.timeControl ?? '10';
    const numeric = parseInt(String(raw).replace(/\D/g, ''), 10);
    return (isNaN(numeric) ? 10 : numeric) * 60;
  }, [matchData?.timeControl]);

  const [timeLeft, setTimeLeft] = useState(initialTimeSeconds);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<Record<number, string>>({});
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'waiting' | 'completed' | 'error'>('idle');
  const [submitResult, setSubmitResult] = useState<{
    your_score?: number;
    opponent_score?: number;
    winner?: string;
    you_won?: boolean;
    message?: string;
    answers?: any;
  } | null>(null);
  const [reviewAnswers, setReviewAnswers] = useState<Record<number, { correctAnswer?: string; explanation?: string }>>({});
  const pollTimerRef = useRef<number | null>(null);

  // Countdown states
  const [showCountdown, setShowCountdown] = useState(true);
  const [countdownNumber, setCountdownNumber] = useState(3);
  const opponentName = matchData?.opponentName || 'Player';
  const opponentCity = matchData?.opponentCity || 'Unknown';
  const reviewMode = submitStatus === 'completed';

  // Prefer questions from matchData; fall back to static list
  const questions = useMemo(() => matchData?.questions ?? quizQuestions, [matchData?.questions]);

  // Countdown timer effect
  useEffect(() => {
    if (!showCountdown) return;

    if (countdownNumber > 0) {
      const timer = setTimeout(() => {
        setCountdownNumber((prev) => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      // Show "Go!" for 1 second, then hide countdown
      const goTimer = setTimeout(() => {
        setShowCountdown(false);
      }, 1000);
      return () => clearTimeout(goTimer);
    }
  }, [countdownNumber, showCountdown]);

  // Quiz timer effect (starts after countdown)
  useEffect(() => {
    if (showCountdown || timeLeft === 0 || hasSubmitted) return;
    const timer = window.setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [showCountdown, timeLeft, hasSubmitted]);

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;
  const currentAnswerMeta = reviewAnswers[currentQuestion.id] || {};

  const handleOptionSelect = (option: string) => {
    if (reviewMode) return; // disable changes during review
    setSelectedOptions((prev) => ({ ...prev, [currentQuestion.id]: option }));
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleSubmit = () => {
    // Prevent duplicate submits
    if (!matchData?.matchId || isSubmitting) return;

    const submitPayload = {
      submission: selectedOptions,
      time_taken: initialTimeSeconds - timeLeft,
    };

    const processAnswerDetails = (answersPayload: any) => {
      const result: Record<number, { correctAnswer?: string; explanation?: string }> = {};
    
      answersPayload.forEach((q:any) => {
        const correctAnswer = q.options[q.answer]; // answer is the index
        result[q.id] = {
          correctAnswer,
          explanation: q.explanation ?? undefined,
        };
      });
    
      return result;
    };
    const postSubmission = async () => {
      setIsSubmitting(true);
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          setSubmitStatus('error');
          setSubmitResult({ message: 'No access token found. Please log in again.' });
          setIsSubmitting(false);
          return;
        }

        const response = await fetch(`http://prepee.onrender.com/matchmaking/${matchData.matchId}/submit-answer/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(submitPayload),
        });

        const data = await response.json();

        if (!response.ok) {
          setSubmitStatus('error');
          setSubmitResult({ message: data?.error || 'Submission failed' });
          setIsSubmitting(false);
          return;
        }

        if (data.status === 'waiting') {
          setSubmitStatus('waiting');
          setSubmitResult({ message: data.message || 'Waiting for opponent...' });
          // Start polling until opponent submits
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          pollTimerRef.current = window.setInterval(async () => {
            try {
              const pollRes = await fetch(`http://prepee.onrender.com/matchmaking/${matchData.matchId}/submit-answer/`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(submitPayload),
              });
              const pollData = await pollRes.json();
              if (pollData.status === 'completed') {
                clearInterval(pollTimerRef.current!);
                pollTimerRef.current = null;
                setSubmitStatus('completed');
                setSubmitResult({
                  your_score: pollData.your_score,
                  opponent_score: pollData.opponent_score,
                  winner: pollData.winner,
                  you_won: pollData.you_won,
                  answers: pollData.answers,
                });
                setReviewAnswers(processAnswerDetails(pollData.answers));
                setHasSubmitted(true);
                setIsSubmitting(false);
              }
            } catch (err) {
              console.error('Polling error:', err);
            }
          }, 2000);
        } else if (data.status === 'completed') {
          setSubmitStatus('completed');
          setSubmitResult({
            your_score: data.your_score,
            opponent_score: data.opponent_score,
            winner: data.winner,
            you_won: data.you_won,
            answers: data.answers,
          });
          setReviewAnswers(processAnswerDetails(data.answers));
          setHasSubmitted(true);
          setIsSubmitting(false);
        } else {
          setSubmitStatus('error');
          setSubmitResult({ message: 'Unexpected response' });
          setIsSubmitting(false);
        }
      } catch (error) {
        console.error('Submit error:', error);
        setSubmitStatus('error');
        setSubmitResult({ message: 'Network error while submitting' });
        setIsSubmitting(false);
      }
    };

    postSubmission();
  };

  // Cleanup polling timer on unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Countdown Overlay */}
      {showCountdown && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/95 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-6">
            <div className="text-center">
              <p className="text-xl text-slate-300 mb-2">
                Matched with <span className="font-semibold text-white">{opponentName}</span> from <span className="font-semibold text-white">{opponentCity}</span>
              </p>
              <p className="text-lg text-slate-400">Match starting in</p>
            </div>
            {countdownNumber > 0 ? (
              <div className="text-8xl font-bold text-indigo-400 animate-pulse">
                {countdownNumber}
              </div>
            ) : (
              <div className="text-8xl font-bold text-emerald-400 animate-bounce">
                Go!
              </div>
            )}
          </div>
        </div>
      )}

      <header className="border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2 text-xl font-semibold tracking-tight">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 text-2xl text-indigo-300">
              ⚡
            </span>
            Quiz Session
          </div>
          <div className="flex flex-col items-end">
            <span className="text-xs uppercase tracking-[0.3em] text-slate-400">Time Left</span>
            <div className="mt-1 rounded-full border border-indigo-400/70 px-5 py-2 text-lg font-semibold tracking-wide text-white">
              {formatTime(timeLeft)}
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-10">
        <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-indigo-500/10">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>
              Question {currentIndex + 1} / {questions.length}
            </span>
            <span className="text-indigo-300">{currentQuestion.category}</span>
          </div>

          <h2 className="mt-4 text-2xl font-semibold leading-tight">{currentQuestion.question}</h2>

          <div className="mt-6 space-y-3">
            {currentQuestion.options.map((option) => {
              const isSelected = selectedOptions[currentQuestion.id] === option;
              const correctAnswer = currentAnswerMeta.correctAnswer;
              const isCorrectOption = reviewMode && correctAnswer === option;
              const isUserWrongSelection = reviewMode && isSelected && !isCorrectOption;
              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => handleOptionSelect(option)}
                  disabled={reviewMode}
                  className={`w-full rounded-2xl border px-4 py-4 text-left text-base transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                    reviewMode
                      ? isCorrectOption
                        ? 'border-emerald-400 bg-emerald-500/20 text-white shadow-lg shadow-emerald-500/30'
                        : isUserWrongSelection
                          ? 'border-rose-400 bg-rose-500/10 text-white'
                          : 'border-white/10 bg-white/5 text-slate-200'
                      : isSelected
                        ? 'border-indigo-400 bg-indigo-500/20 text-white shadow-lg shadow-indigo-500/30'
                        : 'border-white/10 bg-white/5 text-slate-200 hover:border-indigo-200/60 hover:bg-white/10'
                  }`}
                >
                  {option}
                </button>
              );
            })}
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className="flex-1 rounded-2xl border border-white/20 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-white transition disabled:cursor-not-allowed disabled:border-white/5 disabled:text-slate-500 hover:border-indigo-300/70"
            >
              Previous Question
            </button>

            {!isLastQuestion && (
              <button
                type="button"
                onClick={handleNext}
                disabled={currentIndex === questions.length - 1}
                className="flex-1 rounded-2xl bg-indigo-500 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
              >
                Next Question
              </button>
            )}

            {isLastQuestion && (
              <button
                type="button"
                onClick={handleSubmit}
                className="flex-1 rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-white shadow-lg shadow-emerald-500/30 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:bg-slate-700"
                disabled={hasSubmitted || isSubmitting || reviewMode}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Quiz'}
              </button>
            )}
          </div>

          {submitStatus === 'waiting' && (
            <p className="mt-4 rounded-2xl border border-amber-400/40 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
              {submitResult?.message || 'Waiting for opponent...'}
            </p>
          )}

          {submitStatus === 'completed' && (
            <div className="mt-4 rounded-2xl border border-emerald-400/40 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
              <p className="font-semibold text-white">Match completed!</p>
              <p>Your score: {submitResult?.your_score ?? '-'}</p>
              <p>Opponent score: {submitResult?.opponent_score ?? '-'}</p>
              {submitResult?.winner && (
                <p>Winner: {submitResult.winner}</p>
              )}
              {submitResult?.you_won !== undefined && (
                <p>{submitResult.you_won ? 'You won! 🎉' : 'Better luck next time.'}</p>
              )}
            </div>
          )}

          {submitStatus === 'error' && (
            <p className="mt-4 rounded-2xl border border-rose-400/40 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
              {submitResult?.message || 'Submission failed. Please try again.'}
            </p>
          )}

          {reviewMode && (
            <div className="mt-6 rounded-2xl border border-indigo-400/40 bg-indigo-500/10 px-4 py-4 text-sm text-slate-100">
              <p className="font-semibold text-white">Explanation</p>
              <p className="mt-2 text-slate-200">
                {currentAnswerMeta.explanation || 'No explanation provided.'}
              </p>
              {currentAnswerMeta.correctAnswer && (
                <p className="mt-2 text-emerald-200">
                  Correct answer: <span className="font-semibold text-white">{currentAnswerMeta.correctAnswer}</span>
                </p>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}