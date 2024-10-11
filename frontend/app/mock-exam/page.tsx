"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import QuestionComponent from "../components/MockExam/QuestionComponent";
import TimerComponent from "../components/MockExam/TimerComponent";
import { Question } from "../components/MockExam/types";

//const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://3.89.115.184:8000';
const QUESTIONS_PER_PAGE = 10; // Change this to 5 if you want 5 questions per page

const MockExamPage = () => {
  const router = useRouter();
  
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(7200); // 120 minutes in seconds
  const [isTimerExpired, setIsTimerExpired] = useState(false);

  const fetchExamData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/mock_exam`, {
        method: "GET",
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (!Array.isArray(data.questions) || data.questions.length === 0) {
        throw new Error('Invalid or empty question data received');
      }
      setQuestions(data.questions);
    } catch (error) {
      console.error("Error fetching mock exam data:", error);
      setError("Failed to load exam questions. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExamData();
  }, [fetchExamData]);

  const handleAnswerSelect = useCallback((questionId: string, answer: string) => {
    setSelectedAnswers(prev => ({ ...prev, [questionId]: answer }));
  }, []);

  const handleNavigation = useCallback((direction: 'next' | 'prev') => {
    setCurrentPage(prevPage => {
      if (direction === 'next' && (prevPage + 1) * QUESTIONS_PER_PAGE < questions.length) {
        return prevPage + 1;
      } else if (direction === 'prev' && prevPage > 0) {
        return prevPage - 1;
      }
      return prevPage;
    });
  }, [questions.length]);

  const handleSubmitExam = useCallback(() => {
    localStorage.setItem("selectedAnswers", JSON.stringify(selectedAnswers));
    localStorage.setItem("mockExamQuestions", JSON.stringify(questions));
    router.push("/exam_summary");
  }, [selectedAnswers, questions, router]);

  const handleTimerExpire = useCallback(() => {
    setIsTimerExpired(true);
    handleSubmitExam();
  }, [handleSubmitExam]);

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading exam questions...</div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <p className="text-red-500 mb-4">{error}</p>
        <button 
          onClick={fetchExamData}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  const currentQuestions = questions.slice(currentPage * QUESTIONS_PER_PAGE, (currentPage + 1) * QUESTIONS_PER_PAGE);

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">UPSC Mock Exam</h1>
      
      <TimerComponent duration={timeRemaining} onExpire={handleTimerExpire} />

      {currentQuestions.map((question) => (
        <QuestionComponent
          key={question.global_questionID}
          question={question}
          onAnswerSelect={handleAnswerSelect}
          selectedAnswer={selectedAnswers[question.global_questionID]}
          disabled={isTimerExpired}
        />
      ))}

      <div className="flex justify-between mt-4">
        <button
          onClick={() => handleNavigation('prev')}
          disabled={currentPage === 0 || isTimerExpired}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
        >
          Previous
        </button>
        <span>{`Page ${currentPage + 1} of ${Math.ceil(questions.length / QUESTIONS_PER_PAGE)}`}</span>
        {(currentPage + 1) * QUESTIONS_PER_PAGE >= questions.length ? (
          <button
            onClick={handleSubmitExam}
            disabled={isTimerExpired}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
          >
            Submit Exam
          </button>
        ) : (
          <button
            onClick={() => handleNavigation('next')}
            disabled={isTimerExpired}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
};

export default MockExamPage;