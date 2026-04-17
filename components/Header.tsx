import React from 'react';

const Header = () => {
  return (
    <header className="w-full py-6 px-8 border-b border-gray-200 flex justify-between items-center bg-white/80 backdrop-blur-md sticky top-0 z-50">
      <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
        New Project
      </div>
      <nav>
        <ul className="flex gap-6 text-sm font-medium text-gray-600">
          <li className="hover:text-blue-600 cursor-pointer transition-colors">Home</li>
          <li className="hover:text-blue-600 cursor-pointer transition-colors">About</li>
          <li className="hover:text-blue-600 cursor-pointer transition-colors">Contact</li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;
