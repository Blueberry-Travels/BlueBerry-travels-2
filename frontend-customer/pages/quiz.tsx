import React, { useState, useCallback } from 'react';
import Head from 'next/head';
import api from '../lib/api';

/* ── Quiz Data ── */
interface QuizOption {
  label: string;
  weights: Record<string, number>;
}

interface QuizQuestion {
  label: string;
  text: string;
  options: QuizOption[];
}

const QUESTIONS: QuizQuestion[] = [
  {
    label: 'MOMENT 1 OF 5',
    text: 'What does your ideal morning look like?',
    options: [
      { label: '⛰ Sunrise at a mountain peak after a night trek',        weights: { adventure: 3, chill: 0, explore: 1, experience: 1 } },
      { label: '🌞 Slow chai and a book by a river',                     weights: { adventure: 0, chill: 3, explore: 0, experience: 1 } },
      { label: '🍗 Exploring a local market and tasting breakfast',      weights: { adventure: 0, chill: 0, explore: 3, experience: 2 } },
      { label: '💻 Early call done, rest of day free',                   weights: { adventure: 0, chill: 2, explore: 1, experience: 0 } },
    ],
  },
  {
    label: 'MOMENT 2 OF 5',
    text: 'Your travel group is usually…',
    options: [
      { label: '👤 Solo — just me',                                     weights: { adventure: 2, chill: 1, explore: 2, experience: 0 } },
      { label: '💑 With my partner',                                    weights: { adventure: 1, chill: 2, explore: 1, experience: 1 } },
      { label: '👥 Small group of close friends',                       weights: { adventure: 2, chill: 0, explore: 1, experience: 2 } },
      { label: '👪 Family with kids',                                   weights: { adventure: 0, chill: 2, explore: 1, experience: 2 } },
    ],
  },
  {
    label: 'MOMENT 3 OF 5',
    text: 'How do you feel about itineraries?',
    options: [
      { label: '📅 I like every hour planned — no surprises',           weights: { adventure: 0, chill: 1, explore: 0, experience: 2 } },
      { label: '⚙ Broad plan, flexible on details',                    weights: { adventure: 1, chill: 1, explore: 2, experience: 1 } },
      { label: '🏠 Just a base — I\'ll figure it out',                  weights: { adventure: 2, chill: 0, explore: 3, experience: 0 } },
    ],
  },
  {
    label: 'MOMENT 4 OF 5',
    text: 'What\'s your budget comfort zone?',
    options: [
      { label: '💲 Budget — conscious and smart',               weights: { adventure: 2, chill: 1, explore: 2, experience: 0 } },
      { label: '💵 Mid-range — balance of comfort and cost',                        weights: { adventure: 1, chill: 1, explore: 1, experience: 1 } },
      { label: '💰 Premium — quality and exclusivity matter',          weights: { adventure: 0, chill: 2, explore: 0, experience: 3 } },
    ],
  },
  {
    label: 'MOMENT 5 OF 5',
    text: 'What do you most want to come home with?',
    options: [
      { label: '📷 Photographs and stories',                            weights: { adventure: 2, chill: 0, explore: 2, experience: 1 } },
      { label: '🌟 A feeling of having truly rested',                   weights: { adventure: 0, chill: 3, explore: 0, experience: 1 } },
      { label: '🌟 New skills or knowledge',                            weights: { adventure: 1, chill: 0, explore: 2, experience: 2 } },
      { label: '💌 A memory I\'ll talk about for years',                weights: { adventure: 2, chill: 0, explore: 1, experience: 3 } },
    ],
  },
];

interface Profile {
  emoji: string;
  title: string;
  desc: string;
  cta: string;
  ctaHref: string;
}

const PROFILES: Record<string, Profile> = {
  adventure:  { emoji: '🏔️', title: "The High-Altitude Maverick",   desc: 'You crave adrenaline and wild terrain. Treks, rapids, and sunrise scrambles are your fuel.', cta: 'Explore Adventures', ctaHref: '/retreats' },
  chill:      { emoji: '🧘', title: "The Zen Seeker",    desc: 'You travel to unwind. A hammock, a book, and no agenda — that\'s the dream.', cta: 'Browse Retreats',    ctaHref: '/retreats' },
  explore:    { emoji: '🗺️', title: "The Soul Explorer",     desc: 'You crave depth over distance. You want to go off the beaten path and meet real people.', cta: 'Start Discovery', ctaHref: '/hobbyist' },
  experience: { emoji: '✨', title: "The Curated Connoisseur",   desc: 'You seek premium, expert-led experiences — heritage stays and stories behind the landmarks.', cta: 'Browse Packages',    ctaHref: '/packages' },
};

export default function Quiz() {
  const [currentQ, setCurrentQ]   = useState(0);
  const [answers, setAnswers]     = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult]       = useState<Profile | null>(null);

  const scoreFallback = useCallback((allAnswers: number[]) => {
    const totals: Record<string, number> = { adventure: 0, chill: 0, explore: 0, experience: 0 };
    allAnswers.forEach((optIdx, qIdx) => {
      const w = QUESTIONS[qIdx].options[optIdx].weights;
      Object.keys(w).forEach(k => { totals[k] += w[k]; });
    });
    const winner = Object.entries(totals).sort((a, b) => b[1] - a[1])[0][0];
    return PROFILES[winner] || PROFILES.explore;
  }, []);

  const handleAnswer = useCallback(async (optionIdx: number) => {
    const newAnswers = [...answers, optionIdx];
    setAnswers(newAnswers);

    if (currentQ < QUESTIONS.length - 1) {
      setCurrentQ(prev => prev + 1);
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        answers: newAnswers.map((optIdx, qIdx) => ({
          question_index: qIdx,
          option_index: optIdx,
          weights: QUESTIONS[qIdx].options[optIdx].weights,
        })),
      };
      const res = await api.post('/api/v1/quiz/submit/', payload);
      const key = res.data.profile as string;
      setResult(PROFILES[key] || scoreFallback(newAnswers));
    } catch {
      setResult(scoreFallback(newAnswers));
    } finally {
      setSubmitting(false);
    }
  }, [answers, currentQ, scoreFallback]);

  const progress = result ? 100 : ((currentQ) / QUESTIONS.length) * 100;

  return (
    <>
      <Head>
        <title>Discovery Quiz — Blueberry Travels</title>
      </Head>

      <div className="hero-image" style={{ backgroundImage: `url('/hero_quiz.png')`, height: '40vh', minHeight: '350px' }}>
          <div className="hero-overlay"></div>
          <div className="hero-content">
              <span className="hero-badge">Style Finder</span>
              <h1 className="hero-title">Who Are You?</h1>
              <p className="hero-subtitle">Answer 5 questions and we'll reveal your true travel persona.</p>
          </div>
      </div>

      <div className="quiz-container">
          <div className="quiz-progress-bar">
              <div className="quiz-progress-fill" style={{ width: `${progress}%` }}></div>
          </div>

          <div className="quiz-card-wrapper">
              {result ? (
                  <div className="result-screen glass-dark">
                      <div className="result-emoji">{result.emoji}</div>
                      <h2 className="result-title">{result.title}</h2>
                      <p className="result-desc">{result.desc}</p>
                      <div className="result-actions">
                          <button className="btn-primary" onClick={() => window.location.href = result.ctaHref}>{result.cta}</button>
                          <button className="btn-secondary" onClick={() => { setCurrentQ(0); setAnswers([]); setResult(null); }}>Retake</button>
                      </div>
                  </div>
              ) : submitting ? (
                  <div className="loading-screen glass">
                      <div className="loading-icon">🫐</div>
                      <p>Mapping your soul to the mountains...</p>
                  </div>
              ) : (
                  <div className="question-card glass">
                      <span className="q-label">{QUESTIONS[currentQ].label}</span>
                      <h2 className="q-text">{QUESTIONS[currentQ].text}</h2>
                      <div className="options-list">
                          {QUESTIONS[currentQ].options.map((opt, idx) => (
                              <button key={idx} className="option-btn" onClick={() => handleAnswer(idx)}>
                                  {opt.label}
                              </button>
                          ))}
                      </div>
                  </div>
              )}
          </div>
      </div>

      <style jsx>{`
        .quiz-container {
            max-width: 700px;
            margin: -60px auto 100px;
            padding: 0 24px;
            position: relative;
            z-index: 10;
        }
        
        .quiz-progress-bar {
            height: 4px; background: rgba(255,255,255,0.05);
            border-radius: 100px; margin-bottom: 40px; overflow: hidden;
        }
        .quiz-progress-fill {
            height: 100%; background: var(--primary);
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 15px var(--primary);
        }
        
        .question-card, .result-screen, .loading-screen {
            padding: 56px; border-radius: 40px; text-align: center;
        }
        
        .q-label { font-size: 11px; font-weight: 800; color: var(--primary-light); text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 16px; display: block; }
        .q-text { font-size: clamp(24px, 4vw, 32px); color: white; margin-bottom: 40px; line-height: 1.2; letter-spacing: -0.02em; }
        
        .options-list { display: flex; flex-direction: column; gap: 16px; }
        .option-btn {
            background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
            padding: 24px; border-radius: 20px; color: white; font-size: 16px; font-weight: 600;
            text-align: left; cursor: pointer; transition: 0.3s;
        }
        .option-btn:hover { background: rgba(255,255,255,0.08); border-color: var(--primary-light); transform: translateX(8px); }
        
        .result-emoji { font-size: 72px; margin-bottom: 24px; }
        .result-title { font-size: 32px; color: white; margin-bottom: 16px; }
        .result-desc { font-size: 16px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 40px; }
        .result-actions { display: flex; gap: 16px; justify-content: center; }
        
        .loading-screen { padding: 100px 0; }
        .loading-icon { font-size: 48px; margin-bottom: 24px; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } }
      `}</style>
    </>
  );
}
