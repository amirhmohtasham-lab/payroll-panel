import { NavLink, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';

interface NavItem {
  to: string;
  icon: string;
  label: string;
}

export function Layout({
  title,
  navItems,
  children,
}: {
  title: string;
  navItems: NavItem[];
  children: ReactNode;
}) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <img src="/favicon.svg" alt="" aria-hidden="true" />
          <span>گندم دشت</span>
        </div>
        <div className="sidebar-note">
          <span className="sidebar-note-mark" aria-hidden="true" />
          <span>سامانه مالی مزرعه</span>
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </aside>
      <div className="content">
        <header className="topbar">
          <div className="topbar-heading">
            <span className="topbar-kicker">دفتر عملیات • امروز</span>
            <h1>{title}</h1>
          </div>
          <div className="left">
            <span className="user-chip"><span className="user-dot" aria-hidden="true" />{user?.name}</span>
            <button className="secondary" onClick={handleLogout}>
              خروج
            </button>
          </div>
        </header>
        <main className="page">{children}</main>
      </div>
    </div>
  );
}
