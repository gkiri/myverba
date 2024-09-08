import React, { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronDown, Info } from 'lucide-react';
import { insertSampleGS1Data } from '../../utils/insertSampleGS1Data';

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

interface Chapter {
  id: string;
  title: string;
  progress: number;
  children?: Chapter[];
  status: string;
  last_activity: string;
  mock_exam_scores: number[];
}

interface SyllabusViewerProps {
  APIHost: string | null;
  production: boolean;
}

const SyllabusViewer: React.FC<SyllabusViewerProps> = ({ APIHost, production }) => {
  const [gs1Data, setGS1Data] = useState<GS1Data | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchGS1Data = async () => {
      setIsLoading(true);
      const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
      const { data: userData } = await supabase.auth.getUser();
      const userId = userData.user?.id;

      if (!userId) {
        console.error('User not authenticated');
        setIsLoading(false);
        return;
      }

      try {
        let { data, error } = await supabase
          .from('gs1_progress')
          .select('*')
          .eq('user_id', userId)
          .single();

        if (error) {
          if (error.code === 'PGRST116') {
            console.log('No existing GS1 data found, inserting sample data');
            data = await insertSampleGS1Data(userId);
          } else {
            throw error;
          }
        }

        if (data) {
          console.log('Fetched or inserted GS1 data:', data);
          setGS1Data(data);
        } else {
          console.error('Error fetching or inserting GS1 data');
        }
      } catch (error) {
        console.error('Error in fetchGS1Data:', error);
      }

      setIsLoading(false);
    };

    fetchGS1Data();
  }, []);

  const transformGS1DataToChapter = (data: GS1Data | null): Chapter => {
    if (!data) {
      console.log('No GS1 data available');
      return { id: 'root', title: 'GS1 Syllabus', progress: 0, status: '', last_activity: '', mock_exam_scores: [], children: [] };
    }

    console.log('Transforming GS1 data:', data);

    const chapters: Chapter[] = [
      'h1', 'h2', 'h3', 'g1', 'g2', 'g3'
    ].map(chapterId => {
      const chapterData = data[chapterId] as ChapterProgress;
      return {
        id: chapterId,
        title: `Chapter ${chapterId.toUpperCase()}`,
        progress: chapterData ? calculateProgress(chapterData.status) : 0,
        status: chapterData ? chapterData.status : 'not_started',
        last_activity: chapterData ? chapterData.last_activity || '' : '',
        mock_exam_scores: chapterData ? chapterData.mock_exam_scores || [] : [],
      };
    });

    const rootChapter: Chapter = {
      id: 'root',
      title: 'GS1 Syllabus',
      progress: Math.round(chapters.reduce((acc, chapter) => acc + chapter.progress, 0) / chapters.length),
      children: chapters,
      status: '',
      last_activity: '',
      mock_exam_scores: [],
    };

    console.log('Transformed syllabus data:', rootChapter);
    return rootChapter;
  };

  const calculateProgress = (status: string): number => {
    switch (status) {
      case 'completed':
        return 100;
      case 'in_progress':
        return 50;
      case 'not_started':
        return 0;
      default:
        return 0;
    }
  };

  const TreeNode: React.FC<{ node: Chapter, level: number }> = ({ node, level }) => {
    const [isOpen, setIsOpen] = useState(level === 0);
    const [showInfo, setShowInfo] = useState(false);

    const toggleOpen = () => setIsOpen(!isOpen);

    const nodeColor = node.progress >= 80 ? 'bg-green-500' : 
                      node.progress >= 40 ? 'bg-yellow-500' : 'bg-red-500';

    const formatDate = (dateString: string) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString();
    };

    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
        className={`ml-${level * 4} mb-2`}
      >
        <div className="flex items-center space-x-2">
          {node.children && node.children.length > 0 && (
            <button
              onClick={toggleOpen}
              className="text-blue-400 hover:text-blue-300 transition-colors duration-200"
            >
              {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
          )}
          {(!node.children || node.children.length === 0) && <div className="w-4"></div>}
          <motion.div 
            className={`w-4 h-4 rounded-full ${nodeColor}`}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
          />
          <span className="text-white font-medium">{node.title}</span>
          <div className="flex-grow h-0.5 bg-gray-600" />
          <span className="text-gray-400 text-sm">{node.progress}%</span>
          <button
            onClick={() => setShowInfo(!showInfo)}
            className="text-gray-400 hover:text-gray-300 transition-colors duration-200"
          >
            <Info size={16} />
          </button>
        </div>
        <AnimatePresence>
          {showInfo && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="ml-6 mt-2 p-2 bg-gray-700 rounded text-sm text-gray-300"
            >
              <p>Status: {node.status}</p>
              <p>Last activity: {formatDate(node.last_activity)}</p>
              <p>Mock exam scores: {node.mock_exam_scores.join(', ') || 'N/A'}</p>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {isOpen && node.children && node.children.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-2"
            >
              {node.children.map((child, index) => (
                <React.Fragment key={child.id}>
                  <TreeNode node={child} level={level + 1} />
                  {index < node.children.length - 1 && (
                    <div className="border-b border-gray-700 my-2"></div>
                  )}
                </React.Fragment>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  };

  const syllabusData = transformGS1DataToChapter(gs1Data);

  return (
    <div className="h-full overflow-auto bg-gray-900 text-white p-4 rounded-lg">
      <h1 className="text-2xl font-bold mb-4 text-center bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
        GS1 History Syllabus Tree
      </h1>
      <div className="bg-gray-800 rounded-lg p-4 shadow-xl">
        {isLoading ? (
          <p>Loading syllabus data...</p>
        ) : syllabusData.children && syllabusData.children.length > 0 ? (
          <TreeNode node={syllabusData} level={0} />
        ) : (
          <p>No syllabus data available. Please try refreshing the page.</p>
        )}
      </div>
    </div>
  );
};

export default SyllabusViewer;
