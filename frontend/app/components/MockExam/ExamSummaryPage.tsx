"use client";

import React, { useState, useEffect } from "react";
import { Question } from "./types";

const ExamSummaryPage: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});

  useEffect(() => {
    const storedQuestions = localStorage.getItem("mockExamQuestions");
    const storedAnswers = localStorage.getItem("selectedAnswers");

    if (storedQuestions && storedAnswers) {
      setQuestions(JSON.parse(storedQuestions));
      setSelectedAnswers(JSON.parse(storedAnswers));
    } 
  }, []); 

  return (
    <div className="flex flex-col gap-5 p-5">
      <h2 className="text-2xl font-bold mb-4">Exam Summary</h2>

      {questions.map((question) => (
        <div key={question.global_questionID} className="flex flex-col gap-2 p-4 bg-bg-alt-verba rounded-lg shadow-lg mb-4">
          <p className="font-bold text-lg">{question.question}</p>

          {/* Display User's Answer */}
          <p className="mt-2">
            Your Answer: <span className="font-semibold">{selectedAnswers[question.global_questionID] || "Not Answered"}</span>
          </p>

          {/* Display Correct Answer */}
          <p>
            Correct Answer: <span className="font-semibold text-green-500">{question.answer_key}</span>
          </p>

          {/* Explanation */}
          {question.explanation && (
            <p className="mt-3 italic text-sm text-text-alt-verba">Explanation: {question.description}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default ExamSummaryPage;