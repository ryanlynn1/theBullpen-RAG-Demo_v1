import React from 'react';

interface BullpenIconProps {
  className?: string;
  width?: number;
  height?: number;
}

const BullpenIcon: React.FC<BullpenIconProps> = ({ 
  className = "", 
  width = 188, 
  height = 179 
}) => {
  return (
    <svg 
      width={width} 
      height={height} 
      viewBox="0 0 188 179" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <g clipPath="url(#clip0_726_11509)">
        <rect x="73" y="111" width="41" height="10" fill="currentColor"/>
        <circle cx="65" cy="120" r="25" fill="currentColor"/>
        <circle cx="119.5" cy="120.5" r="25.5" fill="currentColor"/>
        <circle cx="120" cy="121" r="17" fill="#26A8E2"/>
        <circle cx="65" cy="121" r="17" fill="#8AC33F"/>
        <path d="M73 150L114 156V160H73V150Z" fill="currentColor"/>
        <path d="M43.8094 90.0102C42.4917 71.889 130.521 58.6279 141.692 73.4566" stroke="currentColor" strokeWidth="6"/>
        <path d="M81.8793 70.814C128.011 91.8947 142.657 67.714 133.979 62.0031" stroke="currentColor" strokeWidth="6"/>
        <path d="M130.572 63.2365C155.889 40.9141 114.836 81.0014 83.7882 62.8255" stroke="currentColor" strokeWidth="6"/>
        <path d="M34 42L145 63.3333V70.1747L42.7249 74L34 42Z" fill="currentColor"/>
        <path d="M34 42L50 71.411L46.0626 94.5319L41.2 98L34 42Z" fill="currentColor"/>
        <path d="M153 45.5L132 67.3331L140.054 98.3478L150 103L153 45.5Z" fill="currentColor"/>
        <path d="M154 42L69.9994 57.5V66.8L151.148 73L154 42Z" fill="currentColor"/>
        <path d="M54 19L46.3896 52.9062L37 61.675L99 68L54 19Z" fill="currentColor"/>
        <path d="M89.5 25.5L70.3896 53.9062L61 62.675L123 69L89.5 25.5Z" fill="currentColor"/>
        <path d="M124.245 28.1197L101.5 51.2937V64L139.5 69.7937L124.245 28.1197Z" fill="currentColor"/>
        <path d="M63 65L46 65.7317V80L68.5 71.5L63 65Z" fill="currentColor"/>
      </g>
      <defs>
        <clipPath id="clip0_726_11509">
          <rect width="188" height="179" fill="white"/>
        </clipPath>
      </defs>
    </svg>
  );
};

export default BullpenIcon; 