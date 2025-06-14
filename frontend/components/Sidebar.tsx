import React from 'react';
import NotepadIcon from './ui/NotepadIcon';

const Sidebar = () => {
  const menuItems = [
    {
      name: 'New chat',
      icon: <NotepadIcon className="w-5 h-5" />,
    },
    {
      name: 'Search chats',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      ),
    },
    {
      name: 'Library',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
          <rect x="7" y="3" width="14" height="14" rx="2" ry="2" />
          <path d="M3 7v11a2 2 0 0 0 2 2h11" />
        </svg>
      ),
    },
  ];

  return (
    <aside className="w-64 bg-bullpen-charcoal-dark text-white p-4 flex flex-col">
      <nav>
        <ul>
          {menuItems.map((item) => (
            <li key={item.name} className="mb-2">
              <a href="#" className="flex items-center p-2 text-base font-normal text-white rounded-lg hover:bg-bullpen-charcoal transition-colors">
                {item.icon}
                <span className="ml-3">{item.name}</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="mt-auto">
        {/* Placeholder for user/settings at the bottom */}
      </div>
    </aside>
  );
};

export default Sidebar; 