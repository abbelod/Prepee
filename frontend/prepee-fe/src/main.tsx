import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from "react-router";

import { AuthProvider } from './pages/AuthProvider.tsx';

import './index.css'
import App from './App.tsx'
import Login from './pages/Login.tsx';
import Signup from './pages/Signup.tsx';
import AboutPage from './pages/AboutPage.tsx';
import QuizPage from './pages/QuizPage.tsx';
import LeaderboardPage from './pages/Leaderboard.tsx';


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/quiz" element={<QuizPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
      </Routes>
    </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)
