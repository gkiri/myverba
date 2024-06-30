"use client";

import React from 'react';
import { useRouter } from 'next/navigation';

interface MockExamStartPageProps {
  APIHost: string;
  setCurrentPage: (page: string) => void;
}

const MockExamStartPage: React.FC<MockExamStartPageProps> = ({ APIHost,setCurrentPage }) => {

  const router = useRouter();

  const handleStartExam = () => {
    router.push('/mock-exam'); // Navigate to the actual exam page
    //setCurrentPage('MOCK_EXAM'); // Set the currentPage to "MOCK_EXAM"
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-8">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full">
        <h2 className="text-3xl font-bold text-center mb-6 text-blue-500">UPSC Mock Exam</h2>

        {/* Exam Instructions Section */}
        <div className="space-y-4">
          <p className="font-semibold text-lg">Instructions:</p>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li>This mock exam consists of 100 multiple-choice questions (MCQs).</li>
            <li>Each question carries 1 mark.</li>
            <li>You will have 20 minutes to complete the exam.</li>
            <li>The timer will start as soon as you click "Start Exam".</li>
            <li>There is no negative marking.</li>
            <li>You can navigate between questions using the pagination controls.</li>
            <li>Once you submit the exam, you will see a detailed summary of your performance.</li>
          </ul>

          <button 
            onClick={handleStartExam}
            className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition duration-300 ease-in-out"
          >
            Start Exam
          </button>
        </div>
      </div>
    </div>
  );
};

export default MockExamStartPage;