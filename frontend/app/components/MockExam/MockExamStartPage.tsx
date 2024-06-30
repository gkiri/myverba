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
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-xl p-8">
        <h1 className="text-3xl font-bold text-center text-blue-600 mb-8">UPSC Mock Exam</h1>
        
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="bg-blue-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Exam Details</h2>
            <ul className="space-y-2 text-gray-700">
              <li>• 100 multiple-choice questions</li>
              <li>• Covers various UPSC topics</li>
              <li>• No negative marking</li>
              <li>• Timed exam environment</li>
            </ul>
          </div>
          <div className="bg-green-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Time Management</h2>
            <ul className="space-y-2 text-gray-700">
              <li>• Full Exam: 120 minutes</li>
              <li>• Section-wise time limits</li>
              <li>• Timer displayed throughout</li>
              <li>• Auto-submit on time expiry</li>
            </ul>
          </div>
        </div>
        
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Select Exam Type</h2>
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
              <span className="ml-2">Full Exam (120 min)</span>
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
              <span className="ml-2">Quick Practice (30 min)</span>
            </label>
          </div>
        </div>
        
        <button
          onClick={handleStartExam}
          className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition duration-300"
        >
          Start Exam
        </button>
      </div>
    </div>
  );
};

export default MockExamStartPage;