"use client";

import { useAuth } from '../utils/auth';
import { useEffect, useState } from 'react';
import { supabase } from '../utils/supabase';

export default function Dashboard() {
  const { user } = useAuth();
  const [mockExams, setMockExams] = useState([]);

  useEffect(() => {
    if (user) {
      fetchMockExams();
    }
  }, [user]);

  const fetchMockExams = async () => {
    const { data, error } = await supabase
      .from('mock_exams')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching mock exams:', error);
    } else {
      setMockExams(data);
    }
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-2">Welcome, {user.email}</h2>
        <p className="mb-4">Here's an overview of your mock exam performance:</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-blue-100 p-4 rounded-lg">
            <h3 className="font-semibold">Total Exams Taken</h3>
            <p className="text-2xl">{mockExams.length}</p>
          </div>
          {/* Add more statistics cards here */}
        </div>
        <h3 className="text-lg font-semibold mt-6 mb-2">Recent Exams</h3>
        <ul className="divide-y divide-gray-200">
          {mockExams.slice(0, 5).map((exam) => (
            <li key={exam.id} className="py-2">
              <p>{new Date(exam.created_at).toLocaleDateString()}: Score {exam.score}/{exam.total_questions}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}