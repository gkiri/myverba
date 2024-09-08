import React, { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

interface ChapterProgress {
  status: string;
  last_activity: string;
  mock_exam_scores: number[];
}

interface GS1Data {
  id: number;
  user_id: string;
  [key: string]: ChapterProgress | number | string;
}

interface SyllabusViewerProps {
  APIHost: string | null;
  production: boolean;
}

const SyllabusViewer: React.FC<SyllabusViewerProps> = ({ APIHost, production }) => {
  const [gs1Data, setGS1Data] = useState<GS1Data | null>(null);

  useEffect(() => {
    const fetchGS1Data = async () => {
      const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
      const { data, error } = await supabase
        .from('gs1')
        .select('*')
        .single();

      if (error) {
        console.error('Error fetching GS1 data:', error);
      } else {
        setGS1Data(data);
      }
    };

    fetchGS1Data();
  }, []);

  const renderChapterProgress = (chapterKey: string, chapterName: string) => {
    if (!gs1Data) return null;

    const chapterData = gs1Data[chapterKey] as ChapterProgress;
    if (!chapterData) return null;

    return (
      <div key={chapterKey} className="mb-4 p-4 bg-white rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-2">{chapterName}</h3>
        <p>Status: {chapterData.status}</p>
        <p>Last Activity: {new Date(chapterData.last_activity).toLocaleDateString()}</p>
        <p>Mock Exam Scores: {chapterData.mock_exam_scores.join(', ')}</p>
      </div>
    );
  };

  return (
    <div className="h-full overflow-auto bg-gray-100 p-4 rounded-lg">
      <h2 className="text-xl font-bold mb-4">GS-1 Syllabus Progress</h2>
      {renderChapterProgress('h1', 'History Chapter 1')}
      {renderChapterProgress('h2', 'History Chapter 2')}
      {renderChapterProgress('h3', 'History Chapter 3')}
      {renderChapterProgress('g1', 'Geography Chapter 1')}
      {renderChapterProgress('g2', 'Geography Chapter 2')}
      {renderChapterProgress('g3', 'Geography Chapter 3')}
    </div>
  );
};

export default SyllabusViewer;
