"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

const MockExamStartPage = ({ APIHost, setCurrentPage }) => {
  const [examType, setExamType] = useState('full');
  const router = useRouter();

  const handleStartExam = () => {
    localStorage.setItem('examType', examType);
    router.push('/mock-exam');
  };

  return (
    <div className="flex-1 flex items-start justify-center bg-gray-100 overflow-hidden pt-16">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow-xl p-6 m-4">
        <h1 className="text-2xl font-bold text-center text-blue-600 mb-4">UPSC Mock Exam</h1>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Exam Details</h2>
            <ul className="text-sm space-y-1 text-gray-700">
              <li>• 100 MCQs</li>
              <li>• Various UPSC topics</li>
              <li>• No negative marking</li>
              <li>• Timed environment</li>
            </ul>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Time Management</h2>
            <ul className="text-sm space-y-1 text-gray-700">
              <li>• Full Exam: 120 min</li>
              <li>• Section-wise limits</li>
              <li>• Visible timer</li>
              <li>• Auto-submit on expiry</li>
            </ul>
          </div>
        </div>
        
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">Select Exam Type</h2>
          <div className="flex space-x-4">
            <label className="inline-flex items-center">
              <input
                type="radio"
                className="form-radio text-blue-600"
                name="examType"
                value="full"
                checked={examType === 'full'}
                onChange={() => setExamType('full')}
              />
              <span className="ml-2 text-sm">Full Exam (120 min)</span>
            </label>
            <label className="inline-flex items-center">
              <input
                type="radio"
                className="form-radio text-blue-600"
                name="examType"
                value="quick"
                checked={examType === 'quick'}
                onChange={() => setExamType('quick')}
              />
              <span className="ml-2 text-sm">Quick Practice (30 min)</span>
            </label>
          </div>
        </div>
        
        <button
          onClick={handleStartExam}
          className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition duration-300"
        >
          Start Exam
        </button>
      </div>
    </div>
  );
};

export default MockExamStartPage;