import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface Question {
  global_questionID: string;
  options: string[];
  answer_key: string;
  question: string;
  description?: string;
}

const ExamSummaryPage = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [score, setScore] = useState(0);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());

  useEffect(() => {
    const storedQuestions: Question[] = JSON.parse(localStorage.getItem('mockExamQuestions') || '[]');
    const storedAnswers: Record<string, string> = JSON.parse(localStorage.getItem('selectedAnswers') || '{}');

    setQuestions(storedQuestions);
    setSelectedAnswers(storedAnswers);

    // Calculate score
    const correctCount = storedQuestions.reduce((count: number, question: Question) => {
      const correctAnswerText = question.options[question.answer_key.charCodeAt(0) - 97];
      return storedAnswers[question.global_questionID] === correctAnswerText ? count + 1 : count;
    }, 0);

    setScore(correctCount);
  }, []);

  const toggleQuestionExpansion = (questionId: string) => {
    setExpandedQuestions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  const attemptedQuestions = Object.keys(selectedAnswers).length;
  const unattemptedQuestions = questions.length - attemptedQuestions;
  const incorrectAnswers = attemptedQuestions - score;

  const chartData = [
    { name: 'Correct', value: score, color: '#4CAF50' },
    { name: 'Incorrect', value: incorrectAnswers, color: '#F44336' },
    { name: 'Unattempted', value: unattemptedQuestions, color: '#9E9E9E' },
  ];

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-3xl font-bold text-center mb-8">Exam Summary</h1>

      <div className="grid md:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Score Overview</h2>
          <div className="text-4xl font-bold text-center mb-4">
            {score} / {questions.length}
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-green-500 font-semibold">{score}</div>
              <div className="text-sm">Correct</div>
            </div>
            <div>
              <div className="text-red-500 font-semibold">{incorrectAnswers}</div>
              <div className="text-sm">Incorrect</div>
            </div>
            <div>
              <div className="text-gray-500 font-semibold">{unattemptedQuestions}</div>
              <div className="text-sm">Unattempted</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Performance Chart</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Question Review</h2>
        {questions.map((question, index) => {
          const selectedAnswer = selectedAnswers[question.global_questionID];
          const correctAnswerText = question.options[question.answer_key.charCodeAt(0) - 97];
          const isCorrect = selectedAnswer === correctAnswerText;
          const isExpanded = expandedQuestions.has(question.global_questionID);

          return (
            <div key={question.global_questionID} className="mb-4 p-4 border rounded">
              <div className="flex justify-between items-center cursor-pointer" onClick={() => toggleQuestionExpansion(question.global_questionID)}>
                <p className="font-bold">Question {index + 1}</p>
                <span className={`px-2 py-1 rounded-full text-sm ${isCorrect ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                  {isCorrect ? 'Correct' : 'Incorrect'}
                </span>
              </div>
              
              {isExpanded && (
                <div className="mt-2">
                  <p>{question.question}</p>
                  <div className="mt-2">
                    {question.options.map((option, optionIndex) => {
                      const isSelected = selectedAnswer === option;
                      const isCorrectOption = option === correctAnswerText;
                      return (
                        <div key={optionIndex} className={`p-2 ${isSelected ? (isCorrectOption ? 'bg-green-100' : 'bg-red-100') : ''} ${isCorrectOption ? 'font-bold' : ''}`}>
                          {option} {isSelected && '(Selected)'} {isCorrectOption && '(Correct)'}
                        </div>
                      );
                    })}
                  </div>
                  {question.description && (
                    <div className="mt-2 p-2 bg-blue-50">
                      <p className="font-semibold">Explanation:</p>
                      <p>{question.description}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ExamSummaryPage;