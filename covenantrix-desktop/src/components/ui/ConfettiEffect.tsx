/**
 * Confetti Effect Component
 * Celebratory animation for successful PAID tier activation
 */

import React, { useEffect, useState } from 'react';

interface ConfettiEffectProps {
  trigger: boolean;
  onComplete?: () => void;
}

export const ConfettiEffect: React.FC<ConfettiEffectProps> = ({ trigger, onComplete }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (trigger) {
      setIsVisible(true);
      
      // Auto-cleanup after animation completes
      const timer = setTimeout(() => {
        setIsVisible(false);
        onComplete?.();
      }, 3500);

      return () => clearTimeout(timer);
    }
  }, [trigger, onComplete]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {/* Confetti particles - burst from center like a cannon */}
      {Array.from({ length: 100 }, (_, i) => {
        // Generate random angles for burst effect
        const angle = Math.random() * 360;
        
        // More dramatic distance - particles fly further
        const distance = 400 + Math.random() * 600;
        
        // Varied velocity for more natural effect
        const velocity = 1.2 + Math.random() * 1.3;
        
        // Calculate end position based on angle and distance
        const radians = (angle * Math.PI) / 180;
        const endX = Math.cos(radians) * distance;
        const endY = Math.sin(radians) * distance;
        
        // Add slight gravity effect to some particles
        const gravityOffset = Math.random() * 100;
        
        const colors = [
          'bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500',
          'bg-pink-500', 'bg-orange-500', 'bg-indigo-500', 'bg-teal-500', 'bg-rose-500',
          'bg-cyan-500', 'bg-lime-500', 'bg-fuchsia-500', 'bg-amber-500'
        ];
        
        const shapes = [
          'w-2 h-4', // Tall rectangles
          'w-4 h-2', // Wide rectangles  
          'w-3 h-3', // Squares
          'w-2 h-6', // Very tall rectangles
          'w-6 h-2', // Very wide rectangles
          'w-3 h-5', // Medium tall
        ];
        
        return (
          <div
            key={i}
            className={`confetti-burst absolute ${shapes[i % shapes.length]} ${colors[i % colors.length]}`}
            style={{
              left: '50%',
              top: '50%',
              '--end-x': `${endX}px`,
              '--end-y': `${endY + gravityOffset}px`,
              '--rotation': `${Math.random() * 720 + 360}deg`,
              animationDelay: `${Math.random() * 0.2}s`,
              animationDuration: `${velocity}s`
            } as React.CSSProperties}
          />
        );
      })}
    </div>
  );
};