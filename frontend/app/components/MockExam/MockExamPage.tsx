"use client";

import React, { useState, useEffect } from "react";
import { SettingsConfiguration } from "../Settings/types";
import QuestionComponent from "./QuestionComponent";
import { MockExamData, Question } from "./types"; 
import { useRouter } from "next/navigation"; 
import PulseLoader from "react-spinners/PulseLoader";

interface MockExamPageProps {
  settingConfig: SettingsConfiguration;
  APIHost: string | null;
}

const MockExamPage: React.FC<MockExamPageProps> = ({
  APIHost,
  settingConfig,
}) => {
  const router = useRouter();
  const [questions, setQuestions] = useState<Question[]>([]); 
  const [currentPage, setCurrentPage] = useState(1); 
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({}); 
  const [isLoading, setIsLoading] = useState(true); 

  const questionsPerPage = 3; 

  useEffect(() => {
    
    const fetchExamData = async () => {
      try {
        const response = await fetch(APIHost + "/api/mock_exam", {
          method: "GET",
        });
        const data: MockExamData = await response.json();
        setQuestions(data.questions); 

        // Shuffle questions for randomness (optional)
        // For example, using the Fisher-Yates shuffle algorithm:
        for (let i = questions.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [questions[i], questions[j]] = [questions[j], questions[i]];
        }

      } catch (error) {
        console.error("Error fetching mock exam data:", error);
      } finally {
        setIsLoading(false); 
      }
    };

    fetchExamData();
  }, []); 

  const currentQuestions =
    !isLoading && questions && questions.length > 0
      ? questions.slice(
          (currentPage - 1) * questionsPerPage,
          currentPage * questionsPerPage
        )
      : [];

  const handleAnswerSelect = (questionId: number, answer: string) => {
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

    router.push('/exam_summary'); 
    //router.push('/mock-exam/exam_summary'); // Updated route
    
  };

  return (
    <div className="flex flex-col gap-5 p-5">
      <h2 className="text-2xl font-bold">UPSC Mock Exam</h2>

      {isLoading ? ( 
        <div className="flex items-center justify-center h-64">
          <PulseLoader loading={true} size={12} speedMultiplier={0.75} />
          <p>Loading Questions...</p>
        </div>
      ) : (
        <div>
          {currentQuestions.map((question,index) => ( 
            <QuestionComponent
              key={question.global_questionID}
              question={question}
              onAnswerSelect={handleAnswerSelect}
              selectedAnswer={selectedAnswers[question.global_questionID]}
            />
          ))}
        </div>
      )} 

      {/* Pagination Controls */}
      <div className="join justify-center items-center text-text-verba">
        {currentPage > 1 && (
          <button
            onClick={handlePreviousPage}
            className="join-item btn btn-sm border-none bg-button-verba hover:bg-secondary-verba"
          >
            «
          </button>
        )}
        <button className="join-item btn btn-sm border-none bg-button-verba hover:bg-secondary-verba">
          Page {currentPage}
        </button>
        {currentPage < Math.ceil((questions?.length || 0) / questionsPerPage) && (
          <button
            onClick={handleNextPage}
            className="join-item btn btn-sm border-none bg-button-verba hover:bg-secondary-verba"
          >
            »
          </button>
        )}
      </div>

      {/* Submit Exam Button */}
      <button
        onClick={handleSubmitExam}
        className="btn btn-lg text-base flex gap-2 bg-secondary-verba hover:bg-button-hover-verba text-text-verba"
      >
        Submit Exam
      </button>
    </div>
  );
};

export default MockExamPage;