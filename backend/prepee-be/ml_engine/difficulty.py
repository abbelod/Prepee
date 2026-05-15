"""
Difficulty Score Prediction Engine
===================================
Hybrid system: Rule-based baseline + trained ML models (Random Forest / XGBoost).

Layer 1 (Rule-Based):
  - TextComplexityAnalyzer: Flesch-Kincaid grade level, word length, technical vocab
  - BloomDetector: Keyword-based cognitive level classification
  - SubjectRuleEngine: Subject/topic difficulty multipliers
  - OptionSimilarityAnalyzer: Answer option similarity scoring

Layer 2 (ML):
  - TrainedDifficultyPredictor: Loads .pkl model for refined predictions

Final output: difficulty score 0.0 (very easy) to 1.0 (very hard)
"""
import os
import re
import math
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# LAYER 1: RULE-BASED COMPONENTS
# ─────────────────────────────────────────────

class TextComplexityAnalyzer:
    """Analyzes linguistic complexity of question text using Flesch-Kincaid."""

    TECHNICAL_WORDS = {
        'photosynthesis', 'mitochondria', 'chromosome', 'electronegativity',
        'thermodynamics', 'centripetal', 'hybridization', 'stoichiometry',
        'differentiation', 'integration', 'equilibrium', 'entropy',
        'catalyst', 'isotope', 'refraction', 'diffraction', 'wavelength',
        'amplitude', 'frequency', 'velocity', 'acceleration', 'momentum',
        'torque', 'capacitance', 'inductance', 'impedance', 'conductance',
        'nucleotide', 'ribosome', 'transcription', 'translation', 'allele',
        'phenotype', 'genotype', 'homozygous', 'heterozygous', 'recessive',
        'polynomial', 'quadratic', 'logarithm', 'derivative', 'integral',
        'matrix', 'determinant', 'eigenvalue', 'vector', 'scalar',
        'algorithm', 'complexity', 'binary', 'hexadecimal', 'recursion',
    }

    NEGATION_WORDS = {'not', 'except', 'unless', 'neither', 'nor', 'without', 'cannot', "doesn't", "isn't", "aren't"}

    FORMULA_PATTERNS = [r'[=+\-×÷∑∫√π∞≈≠≤≥]', r'\d+\.\d+', r'[²³⁴⁵⁶⁷⁸⁹⁰]', r'\b\d+\s*[×x]\s*\d+']

    def analyze(self, text):
        words = text.split()
        word_count = len(words)
        sentences = max(1, len(re.split(r'[.?!;]', text)))

        # Flesch-Kincaid Grade Level
        syllable_count = sum(self._count_syllables(w) for w in words)
        avg_words_per_sentence = word_count / sentences
        avg_syllables_per_word = syllable_count / max(1, word_count)
        fk_grade = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59
        fk_score = min(1.0, max(0.0, fk_grade / 16.0))

        # Avg word length
        avg_word_len = sum(len(w) for w in words) / max(1, word_count)
        word_len_score = min(1.0, max(0.0, (avg_word_len - 3) / 7))

        # Technical vocabulary
        tech_count = sum(1 for w in words if w.lower().strip('.,?!;:') in self.TECHNICAL_WORDS)
        tech_score = min(1.0, tech_count / 3)

        # Negation
        neg_count = sum(1 for w in words if w.lower() in self.NEGATION_WORDS)
        neg_score = min(1.0, neg_count / 2)

        # Formula/symbols
        formula_matches = sum(len(re.findall(p, text)) for p in self.FORMULA_PATTERNS)
        formula_score = min(1.0, formula_matches / 3)

        # Composite score
        complexity = (
            fk_score * 0.30 +
            word_len_score * 0.15 +
            tech_score * 0.25 +
            neg_score * 0.15 +
            formula_score * 0.15
        )

        return {
            'complexity_score': round(min(1.0, max(0.0, complexity)), 4),
            'fk_grade': round(fk_grade, 2),
            'word_count': word_count,
            'avg_word_length': round(avg_word_len, 2),
            'technical_terms': tech_count,
            'negation_count': neg_count,
            'formula_present': formula_matches > 0,
        }

    def _count_syllables(self, word):
        word = word.lower().strip('.,?!;:')
        if len(word) <= 2:
            return 1
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e') and count > 1:
            count -= 1
        return max(1, count)


class BloomDetector:
    """Classifies questions by Bloom's Taxonomy cognitive level."""

    BLOOM_KEYWORDS = {
        'recall': {
            'keywords': ['define', 'list', 'state', 'name', 'identify', 'what is', 'which', 'who', 'when', 'where', 'recall', 'label', 'match'],
            'score': 0.20,
        },
        'understand': {
            'keywords': ['explain', 'describe', 'summarize', 'interpret', 'classify', 'discuss', 'distinguish', 'why', 'how does', 'illustrate', 'role of'],
            'score': 0.40,
        },
        'apply': {
            'keywords': ['calculate', 'solve', 'apply', 'compute', 'determine', 'find', 'use', 'convert', 'demonstrate', 'show that', 'derive'],
            'score': 0.60,
        },
        'analyze': {
            'keywords': ['compare', 'contrast', 'analyze', 'differentiate', 'examine', 'categorize', 'distinguish between', 'relate', 'investigate'],
            'score': 0.80,
        },
        'evaluate': {
            'keywords': ['evaluate', 'design', 'propose', 'create', 'formulate', 'assess', 'justify', 'critique', 'recommend', 'predict outcome'],
            'score': 0.95,
        },
    }

    def detect(self, text):
        text_lower = text.lower()

        best_level = 'recall'
        best_score = 0.20

        for level, config in self.BLOOM_KEYWORDS.items():
            for keyword in config['keywords']:
                if keyword in text_lower:
                    if config['score'] > best_score:
                        best_level = level
                        best_score = config['score']
                    break

        return {
            'bloom_level': best_level,
            'bloom_score': best_score,
        }


class SubjectRuleEngine:
    """Applies subject/topic-specific difficulty adjustments."""

    SUBJECT_MULTIPLIERS = {
        'Physics': 1.15,
        'Chemistry': 1.10,
        'Biology': 0.95,
        'Mathematics': 1.10,
        'English': 0.90,
        'Logical Reasoning': 1.05,
        'ECAT': 1.12,
        'MCAT': 1.08,
    }

    TOPIC_MULTIPLIERS = {
        'Modern Physics': 1.30, 'Thermodynamics': 1.25, 'Waves and Optics': 1.10,
        'Electricity': 1.05, 'Mechanics': 0.95,
        'Organic Chemistry': 1.25, 'Physical Chemistry': 1.20,
        'Chemical Bonding': 1.10, 'Atomic Structure': 0.95, 'Inorganic Chemistry': 0.90,
        'Genetics': 1.15, 'Molecular Biology': 1.20, 'Cell Biology': 0.90,
        'Human Physiology': 1.00, 'Ecology': 0.85,
        'Calculus': 1.25, 'Abstract Algebra': 1.30, 'Trigonometry': 1.05,
        'Algebra': 0.90, 'Statistics': 0.95,
        'Reading Comprehension': 1.10, 'Grammar': 0.85, 'Vocabulary': 0.90,
        'Abstract Reasoning': 1.20, 'Pattern Recognition': 0.95, 'Verbal Reasoning': 1.05,
        'Electrical Engineering': 1.15, 'Computer Science': 1.05, 'Mechanical Engineering': 1.20,
        'Human Biology': 1.00, 'Biochemistry': 1.15, 'Anatomy': 0.95,
    }

    def adjust(self, subject, topic):
        subj_mult = self.SUBJECT_MULTIPLIERS.get(subject, 1.0)
        topic_mult = self.TOPIC_MULTIPLIERS.get(topic, 1.0)

        # Normalize to 0-1 range (centered at 0.5 for multiplier=1.0)
        combined = (subj_mult * topic_mult)
        adjustment = min(1.0, max(0.0, (combined - 0.7) / 0.9))

        return {
            'subject_multiplier': subj_mult,
            'topic_multiplier': topic_mult,
            'adjustment_score': round(adjustment, 4),
        }


class OptionSimilarityAnalyzer:
    """Measures how similar answer options are — more similar = harder."""

    def analyze(self, options):
        if not options or len(options) < 2:
            return {'similarity_score': 0.0}

        similarities = []
        for i in range(len(options)):
            for j in range(i + 1, len(options)):
                sim = self._char_similarity(str(options[i]), str(options[j]))
                similarities.append(sim)

        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
        return {'similarity_score': round(avg_sim, 4)}

    def _char_similarity(self, a, b):
        if not a or not b:
            return 0.0
        matches = sum(1 for x, y in zip(a, b) if x == y)
        return matches / max(len(a), len(b))


# ─────────────────────────────────────────────
# HYBRID CALCULATOR
# ─────────────────────────────────────────────

class HybridDifficultyCalculator:
    """Combines all rule-based components + optional trained model."""

    WEIGHTS = {
        'text_complexity': 0.25,
        'bloom_level': 0.30,
        'subject_adjustment': 0.25,
        'option_similarity': 0.10,
        'structure_complexity': 0.10,
    }

    def __init__(self):
        self.text_analyzer = TextComplexityAnalyzer()
        self.bloom_detector = BloomDetector()
        self.subject_engine = SubjectRuleEngine()
        self.option_analyzer = OptionSimilarityAnalyzer()
        self._trained_model = None

    def analyze(self, question):
        """Analyze a Question model instance."""
        text_result = self.text_analyzer.analyze(question.text)
        bloom_result = self.bloom_detector.detect(question.text)
        subject_result = self.subject_engine.adjust(question.subject, question.topic)
        option_result = self.option_analyzer.analyze(question.options)

        rule_based_score = self._calculate_rule_score(
            text_result, bloom_result, subject_result, option_result
        )

        # Try trained model
        ml_score = self._predict_with_model(question, text_result, bloom_result)

        final_score = ml_score if ml_score is not None else rule_based_score

        return {
            'difficulty_score': round(final_score, 4),
            'rule_based_score': round(rule_based_score, 4),
            'ml_score': round(ml_score, 4) if ml_score is not None else None,
            'text_complexity': text_result['complexity_score'],
            'bloom_level': bloom_result['bloom_level'],
            'bloom_score': bloom_result['bloom_score'],
            'subject_adjustment': subject_result['adjustment_score'],
            'option_similarity': option_result['similarity_score'],
            'breakdown': {
                'text': text_result,
                'bloom': bloom_result,
                'subject': subject_result,
                'options': option_result,
            }
        }

    def analyze_text(self, text, options=None, subject='general', topic='general'):
        """Analyze raw text (for the ad-hoc API endpoint)."""
        text_result = self.text_analyzer.analyze(text)
        bloom_result = self.bloom_detector.detect(text)
        subject_result = self.subject_engine.adjust(subject, topic)
        option_result = self.option_analyzer.analyze(options or [])

        score = self._calculate_rule_score(
            text_result, bloom_result, subject_result, option_result
        )

        return {
            'difficulty_score': round(score, 4),
            'text_complexity': text_result['complexity_score'],
            'bloom_level': bloom_result['bloom_level'],
            'subject_adjustment': subject_result['adjustment_score'],
            'option_similarity': option_result['similarity_score'],
            'breakdown': {
                'text': text_result,
                'bloom': bloom_result,
                'subject': subject_result,
                'options': option_result,
            }
        }

    def _calculate_rule_score(self, text_result, bloom_result, subject_result, option_result):
        score = (
            text_result['complexity_score'] * self.WEIGHTS['text_complexity'] +
            bloom_result['bloom_score'] * self.WEIGHTS['bloom_level'] +
            subject_result['adjustment_score'] * self.WEIGHTS['subject_adjustment'] +
            option_result['similarity_score'] * self.WEIGHTS['option_similarity'] +
            text_result['complexity_score'] * 0.5 * self.WEIGHTS['structure_complexity']
        )
        return min(1.0, max(0.0, score))

    def _predict_with_model(self, question, text_result, bloom_result):
        """Try to use trained ML model for prediction."""
        try:
            if self._trained_model is None:
                model_path = Path(__file__).parent / 'trained_models' / 'difficulty_model.pkl'
                if not model_path.exists():
                    return None
                import joblib
                self._trained_model = joblib.load(model_path)

            bloom_encoding = {'recall': 0, 'understand': 1, 'apply': 2, 'analyze': 3, 'evaluate': 4}
            subject_encoding = {
                'Physics': 0, 'Chemistry': 1, 'Biology': 2, 'Mathematics': 3,
                'English': 4, 'Logical Reasoning': 5, 'ECAT': 6, 'MCAT': 7
            }

            # Must match the 10 features used in trainer.py
            from ml_engine.models import QuestionAttempt
            attempts = QuestionAttempt.objects.filter(question=question)
            if attempts.exists():
                times = list(attempts.values_list('time_taken_seconds', flat=True))
                avg_response_time = sum(times) / len(times)
            else:
                avg_response_time = 30.0

            features = np.array([[
                text_result['complexity_score'],           # text_complexity
                bloom_encoding.get(bloom_result['bloom_level'], 0),  # bloom_level_encoded
                subject_encoding.get(question.subject, 0), # subject_encoded
                text_result['word_count'],                  # word_count
                text_result.get('avg_word_length', 4.0),    # avg_word_length
                text_result.get('technical_terms', 0),      # technical_terms
                1 if text_result.get('formula_present', False) else 0,  # formula_present
                text_result.get('negation_count', 0),       # negation_count
                len(question.options) if question.options else 4,  # option_count
                avg_response_time,                          # avg_response_time
            ]])

            prediction = self._trained_model.predict(features)[0]
            return float(min(1.0, max(0.0, prediction)))

        except Exception as e:
            logger.warning(f"ML prediction failed, using rule-based: {e}")
            return None


def per_student_adjustment(base_difficulty, student_profile, subject):
    """Adjust difficulty based on student's weakness in the subject."""
    if not student_profile or not student_profile.subject_strengths:
        return base_difficulty

    student_accuracy = student_profile.subject_strengths.get(subject, 0.5)
    weakness_factor = 1.0 - student_accuracy
    adjusted = base_difficulty * (1.0 + weakness_factor * 0.5)
    return min(1.0, max(0.0, adjusted))
