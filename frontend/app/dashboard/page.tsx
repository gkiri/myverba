"use client";

import { useAuth } from '../components/Auth/AuthConext';
import { useEffect, useState } from 'react';
import { supabase } from '../utils/supabase';
import { Database } from '../../types/supabase';

type ChapterProgress = {
  status: string;
  last_activity: string | null;
  mock_scores: number[];
};

type GS1Progress = {
  id: string;
  user_id: string;
  h1: ChapterProgress | null;
  h2: ChapterProgress | null;
  h3: ChapterProgress | null;
  g1: ChapterProgress | null;
  g2: ChapterProgress | null;
  g3: ChapterProgress | null;
  created_at: string;
  updated_at: string;
};

const getChapterProgress = (progress: GS1Progress, chapter: string): ChapterProgress | null => {
  const chapterData = progress[chapter as keyof GS1Progress];
  return isChapterProgress(chapterData) ? chapterData : null;
};

function isChapterProgress(value: any): value is ChapterProgress {
  return (
    value !== null &&
    typeof value === 'object' &&
    'status' in value &&
    'last_activity' in value &&
    'mock_scores' in value &&
    Array.isArray(value.mock_scores)
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [gs1Progress, setGS1Progress] = useState<GS1Progress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchGS1Progress();
    } else {
      setIsLoading(false);
    }
  }, [user]);

  const fetchGS1Progress = async () => {
    try {
      const { data, error } = await supabase
        .from('gs1_progress')
        .select('*')
        .eq('user_id', user!.id)
        .single();

      if (error) throw error;

      setGS1Progress(data as GS1Progress);
    } catch (error) {
      console.error('Error fetching GS1 progress:', error);
      setError('Failed to load GS1 progress. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center">{error}</div>;
  }

  if (!user) {
    return <div className="text-center">Please log in to view your dashboard.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-2">Welcome, {user.email}</h2>
        <p className="mb-4">Here is an overview of your GS1 progress:</p>
        {gs1Progress && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {['h1', 'h2', 'h3', 'g1', 'g2', 'g3'].map((chapter) => {
              const chapterProgress = getChapterProgress(gs1Progress, chapter);
              return (
                <div key={chapter} className="bg-blue-100 p-4 rounded-lg">
                  <h3 className="font-semibold">Chapter {chapter.toUpperCase()}</h3>
                  {chapterProgress ? (
                    <>
                      <p>Status: {chapterProgress.status}</p>
                      <p>Last Activity: {chapterProgress.last_activity || 'N/A'}</p>
                      <p>Mock Scores: {chapterProgress.mock_scores.length || 0}</p>
                    </>
                  ) : (
                    <p>No data available</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
