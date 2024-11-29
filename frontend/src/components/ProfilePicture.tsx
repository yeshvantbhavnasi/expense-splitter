import React from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';

interface ProfilePictureProps {
  url?: string | null;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  name?: string;
}

const sizeClasses = {
  sm: 'h-8 w-8',
  md: 'h-12 w-12',
  lg: 'h-16 w-16',
};

const ProfilePicture: React.FC<ProfilePictureProps> = ({ 
  url, 
  size = 'md',
  className = '',
  name = 'Profile'
}) => {
  if (!url) {
    return (
      <div 
        className={`bg-blue-100 rounded-full flex items-center justify-center ${sizeClasses[size]} ${className}`}
      >
        <span className="text-blue-600 font-medium">
          {name.charAt(0).toUpperCase()}
        </span>
      </div>
    );
  }

  return (
    <img
      src={url}
      alt={name}
      className={`rounded-full object-cover ${sizeClasses[size]} ${className}`}
    />
  );
};

export default ProfilePicture;
