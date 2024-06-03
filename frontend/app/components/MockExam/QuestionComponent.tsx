"use client";

import React from "react";
import { Question } from "./types";  

interface QuestionComponentProps {
  question: Question;
  onAnswerSelect: (questionId: number, answer: string) => void;
  selectedAnswer: string | undefined;
}

const QuestionComponent: React.FC<QuestionComponentProps> = ({
  question,
  onAnswerSelect,
  selectedAnswer,
}) => {
  return (
    <div className="flex flex-col gap-2 p-4 bg-bg-alt-verba rounded-lg shadow-lg mb-4">
      <p className="font-bold text-lg">{question.text}</p>

      {/* Render Options */}
      {question.options.map((option, index) => (
        <label 
          key={index} 
          // className="label cursor-pointer flex items-center gap-1"// Reduced gap, improved alignment
          className="flex items-center gap-2 cursor-pointer"
        >
          <input 
            type="radio" 
            name={`question-${question.id}`} //  Group radio buttons by question
            value={option} 
            checked={selectedAnswer === option} 
            onChange={() => onAnswerSelect(question.id, option)} 
            className="radio" 
          /> 
          <span>{option}</span>
        </label>
      ))}
    </div>
  );
}; 

export default QuestionComponent;