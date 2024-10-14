import React from 'react';
import { motion } from 'framer-motion';

interface BulletPointsDisplayProps {
  bulletPoints: string[];
}

const BulletPointsDisplay: React.FC<BulletPointsDisplayProps> = ({ bulletPoints }) => {
  return (
    <div className="bg-bg-alt-verba rounded-lg p-6 shadow-lg">
      <h2 className="text-2xl font-bold mb-4 text-primary-verba">Key Points</h2>
      <ul className="space-y-3">
        {bulletPoints.map((point, index) => (
          <motion.li
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="flex items-start"
          >
            <span className="inline-block w-4 h-4 mr-3 mt-1 bg-secondary-verba rounded-full flex-shrink-0"></span>
            <span className="text-text-verba">{point}</span>
          </motion.li>
        ))}
      </ul>
    </div>
  );
};

export default BulletPointsDisplay;