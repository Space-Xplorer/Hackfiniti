import React from 'react';

const GlassCard = ({ children, className = '', animate = true }) => {
  return (
    <div
      className={`
      relative overflow-hidden
      bg-white/40 backdrop-blur-xl
      border border-white/50
      rounded-[3rem]
      shadow-[0_25px_50px_-12px_rgba(75,0,130,0.1)]
      ${animate ? 'animate-in fade-in zoom-in-95 duration-500' : ''}
      ${className}
    `}
    >
      {children}
    </div>
  );
};

export default GlassCard;
