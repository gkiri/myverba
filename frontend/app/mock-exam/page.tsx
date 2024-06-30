"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import PulseLoader from "react-spinners/PulseLoader";
import QuestionComponent from "../components/MockExam/QuestionComponent";
import TimerComponent from "../components/MockExam/TimerComponent";
import { MockExamData, Question } from "../components/MockExam/types";

const API_BASE_URL = 'http://localhost:8000'; // TODO: Make this configurable

const MockExamPage = () => {
  const router = useRouter();
  
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [timeRemaining, setTimeRemaining] = useState(1200); // 20 minutes in seconds
  const [isTimerExpired, setIsTimerExpired] = useState(false);

  const questionsPerPage = 3;

  useEffect(() => {
    const fetchExamData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/mock_exam`, {
          method: "GET",
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: MockExamData = await response.json();

        // Shuffle questions (optional)
        const shuffledQuestions = [...data.questions];
        for (let i = shuffledQuestions.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [shuffledQuestions[i], shuffledQuestions[j]] = [
            shuffledQuestions[j],
            shuffledQuestions[i],
          ];
        }

        setQuestions(shuffledQuestions);
      } catch (error) {
        console.error("Error fetching mock exam data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExamData();
  }, []);

  const currentQuestions = questions.slice(
    (currentPage - 1) * questionsPerPage,
    currentPage * questionsPerPage
  );

  const handleAnswerSelect = (questionId: string, answer: string) => {
    setSelectedAnswers({ ...selectedAnswers, [questionId]: answer });
  };

  const handleNextPage = () => {
    if (currentPage < Math.ceil(questions.length / questionsPerPage)) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleSubmitExam = () => {
    localStorage.setItem("selectedAnswers", JSON.stringify(selectedAnswers));
    localStorage.setItem("mockExamQuestions", JSON.stringify(questions));
    router.push("/exam_summary");
  };

  const handleTimerExpire = () => {
    setIsTimerExpired(true);
    handleSubmitExam(); 
  };

  return (
    <div className="flex flex-col gap-5 p-5">
      <h2 className="text-2xl font-bold">UPSC Mock Exam</h2>

      <TimerComponent duration={timeRemaining} onExpire={handleTimerExpire} />

      {isLoading ? ( 
        <div className="flex items-center justify-center h-64">
          <PulseLoader loading={true} size={12} speedMultiplier={0.75} />
          <p>Loading Questions...</p>
        </div>
      ) : questions.length > 0 ? (
        <div>
          {currentQuestions.map((question) => (
            <QuestionComponent
              key={question.global_questionID}
              question={question}
              onAnswerSelect={handleAnswerSelect}
              selectedAnswer={selectedAnswers[question.global_questionID]}
              disabled={isTimerExpired}
            />
          ))}
        </div>
      ) : (
        <div className="text-center">No questions available.</div>
      )}

      <div className="join justify-center items-center text-text-verba">
        {currentPage > 1 && (
          <button
            onClick={handlePreviousPage}
            className="join-item btn btn-sm border-none bg-button-verba hover:bg-secondary-verba"
            disabled={isTimerExpired}
          >
            «
          </button>
        )}
        <button
          className="join-item btn btn-sm border-none bg-button-verba hover:bg-secondary-verba"
          disabled={isTimerExpired}
        >
          Page {currentPage}
        </button>
        {currentPage < Math.ceil(questions.length / questionsPerPage) && (
          <button
            onClick={handleNextPage}
            className="join-item btn btn-sm border-none bg-button-verba hover:bg-secondary-verba"
            disabled={isTimerExpired}
          >
            »
          </button>
        )}
      </div>

      <button
        onClick={handleSubmitExam} 
        className="btn btn-lg text-base flex gap-2 bg-secondary-verba hover:bg-button-hover-verba text-text-verba"
        disabled={isTimerExpired} 
      >
        Submit Exam
      </button>
    </div>
  );
};

export default MockExamPage;