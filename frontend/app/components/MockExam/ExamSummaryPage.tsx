"use client";

import React, { useState, useEffect } from "react";
import { Question } from "./types";
import { IoChevronDownOutline, IoChevronUpOutline, IoHelpCircleOutline } from 'react-icons/io5'; 

const ExamSummaryPage: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [score, setScore] = useState(0);
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());

  useEffect(() => {
    const storedQuestions = localStorage.getItem("mockExamQuestions");
    const storedAnswers = localStorage.getItem("selectedAnswers");

    if (storedQuestions && storedAnswers) {
      const parsedQuestions = JSON.parse(storedQuestions) as Question[];
      const parsedAnswers = JSON.parse(storedAnswers) as Record<number, string>;

      setQuestions(parsedQuestions);
      setSelectedAnswers(parsedAnswers);

      // Calculate score
      let correctCount = 0;
      parsedQuestions.forEach((question) => {
        const correctAnswerText = question.options[question.answer_key.charCodeAt(0) - 97];
        if (parsedAnswers[question.global_questionID] === correctAnswerText) {
          correctCount++;
        }
      });
      setScore(correctCount);
    }
  }, []);

  const attemptedQuestions = Object.keys(selectedAnswers).length;
  const unattemptedQuestions = questions.length - attemptedQuestions;
  const correctAnswers = score;
  const wrongAnswers = attemptedQuestions - correctAnswers;

  const handleQuestionToggle = (questionId: number) => {
    setExpandedQuestions((prevState) => {
      const newSet = new Set(prevState);
      if (newSet.has(questionId)) {
        newSet.delete(questionId);
      } else {
        newSet.add(questionId);
      }
      return newSet;
    });
  };

  return (
    <div className="flex flex-col gap-5 p-5">
      <h2 className="text-2xl font-bold mb-4 text-center">Exam Summary</h2>

      {/* Summary Box */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-xl font-semibold mb-4 text-center">Scorecard</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-100 p-3 rounded-md">
            <p className="text-gray-600">Attempted:</p>
            <p className="font-semibold text-lg">{attemptedQuestions}</p>
          </div>
          <div className="bg-gray-100 p-3 rounded-md">
            <p className="text-gray-600">Unattempted:</p>
            <p className="font-semibold text-lg">{unattemptedQuestions}</p>
          </div>
          <div className="bg-green-100 p-3 rounded-md">
            <p className="text-green-600">Correct:</p>
            <p className="font-semibold text-lg">{correctAnswers}</p>
          </div>
          <div className="bg-red-100 p-3 rounded-md">
            <p className="text-red-600">Incorrect:</p>
            <p className="font-semibold text-lg">{wrongAnswers}</p>
          </div>
        </div>
        <div className="mt-6 border-t border-gray-200 pt-4">
          <p className="text-center text-xl font-semibold">
            Final Score:{" "}
            <span className="text-2xl text-blue-500">
              {score}/{questions.length}
            </span>
          </p>
        </div>
      </div>

      {/* Question Review Section (Collapsible) */}
      {questions.map((question, index) => {
        const selectedAnswer = selectedAnswers[question.global_questionID];
        const isCorrect = selectedAnswer === question.options[question.answer_key.charCodeAt(0) - 97];
        const isExpanded = expandedQuestions.has(question.global_questionID);

        return (
          <div key={question.global_questionID} className="bg-white rounded-lg shadow-lg p-4 mb-4">
            <div className="flex justify-between items-center cursor-pointer" onClick={() => handleQuestionToggle(question.global_questionID)}>
              <p className="font-bold text-lg">Question {index + 1}</p>
              <span
                className={`px-2 py-1 rounded-full text-sm font-semibold ${
                  isCorrect ? "bg-green-200 text-green-800" : "bg-red-200 text-red-800"
                }`}
              >
                {isCorrect ? "Correct" : "Incorrect"}
              </span>
              {/* Expand/Collapse Icon */}
              {isExpanded ? (
                <IoChevronUpOutline className="text-gray-600" /> 
              ) : (
                <IoChevronDownOutline className="text-gray-600" />
              )}
            </div>
            
            {/* Conditional Rendering for Expanded Question */}
            {isExpanded && ( 
              <div className="mt-3 space-y-2"> 
                <p className="mt-2">{question.question}</p>

                <div className="mt-3 space-y-2">
                  {question.options.map((option, optionIndex) => {
                    const optionLetter = String.fromCharCode(97 + optionIndex); 
                    const isSelected = selectedAnswer === option; 
                    const isCorrectOption = optionLetter === question.answer_key;

                    return (
                      <div key={optionIndex} className="flex items-center">
                        <input
                          type="radio"
                          checked={isSelected}
                          disabled={true} 
                          className="radio mr-2"
                        />
                        <label
                          className={`
                            ${isSelected && isCorrectOption ? "font-semibold text-green-600" : ""} 
                            ${isSelected && !isCorrectOption ? "font-semibold text-red-600" : ""}
                          `}
                        >
                          {option} {isCorrectOption && "(Correct)"}
                        </label>
                      </div>
                    );
                  })}
                </div>

                {/* Enhanced Explanation Section */}
                {question.description && (
                  <div className="mt-4 border-t border-gray-200 pt-3 relative group">
                    <button className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-in-out">
                      <IoHelpCircleOutline className="text-blue-500 text-lg" /> 
                    </button>
                    <p className="text-base text-gray-700 bg-blue-50 p-3 rounded-md shadow-inner">
                      <span className="font-semibold text-blue-500">Explanation:</span> {question.description}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ExamSummaryPage;