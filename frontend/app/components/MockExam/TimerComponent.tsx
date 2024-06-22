"use client";

import React, { useState, useEffect } from 'react';

interface TimerProps {
  duration: number; // Duration in seconds
  onExpire: () => void; 
}

const TimerComponent: React.FC<TimerProps> = ({ duration, onExpire }) => {
  const [timeRemaining, setTimeRemaining] = useState(duration);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining((prevTime) => prevTime - 1); 
    }, 1000); 

    if (timeRemaining <= 0) {
      clearInterval(timer); 
      onExpire(); 
    }

    return () => clearInterval(timer); 
  }, [timeRemaining, onExpire]); 

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;

  return (
    <div className="text-xl font-semibold">
      Time Remaining: {minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}
    </div>
  );
};

export default TimerComponent;