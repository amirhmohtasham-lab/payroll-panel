// App shell — sidebar navigation (with collapsible groups), topbar, logout.

import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Upload, ChartBar, User, Leaf, NavArchive, NavChat, NavFertilizer, NavGreenhouse, ChevronDown, ChevronUp } from '../ui/icons';
import type { NavItem } from '../lib/nav';

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
  const location = useLocation();

  const iconMap: Record<string, React.ReactNode> = {
    'upload': <Upload size={20} />,
    'folder': <NavArchive size={20} />,
    'chart': <ChartBar size={20} />,
    'robot': <NavChat size={20} />,
    'beaker': <NavFertilizer size={20} />,
    'leaf': <NavGreenhouse size={20} />,
    'farm': <Leaf size={20} />,
    'user': <User size={20} />,
  };

  const pathWithSearch = location.pathname + location.search;

  function isActive(target: string): boolean {
    if (target === '/') return location.pathname === '/';
    return pathWithSearch === target || location.pathname.startsWith(target + '/');
  }

  // groups default open when one of their children is active
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    for (const item of navItems) {
      if (item.children?.some((ch) => isActive(ch.to))) init[item.label] = true;
    }
    return init;
  });

  function toggleGroup(label: string) {
    setOpenGroups((prev) => ({ ...prev, [label]: !prev[label] }));
  }

  function renderItem(item: NavItem) {
    const icon = item.icon ? iconMap[item.icon] : null;
    const hasChildren = !!item.children?.length;
    const childrenActive = hasChildren && item.children!.some((ch) => isActive(ch.to));
    const selfActive = item.to ? isActive(item.to) : false;
    const expanded = hasChildren && (openGroups[item.label] || childrenActive);

    if (!hasChildren) {
      return (
        <NavLink
          key={item.to}
          to={item.to!}
          className={({ isActive: act }) => `nav-item${act ? ' active' : ''}`}
        >
          <span>{icon}</span>
          <span>{item.label}</span>
        </NavLink>
      );
    }

    return (
      <div key={item.label} className="nav-group-wrap">
        <button
          type="button"
          className={`nav-item nav-group${selfActive || childrenActive ? ' active' : ''}`}
          onClick={() => {
            if (item.to) navigate(item.to);
            toggleGroup(item.label);
          }}
        >
          <span>{icon}</span>
          <span>{item.label}</span>
          <span style={{ marginRight: 'auto', display: 'inline-flex' }}>
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </span>
        </button>
        {expanded && (
          <div className="nav-children">
            {item.children!.map((ch) => (
              <NavLink
                key={ch.to}
                to={ch.to}
                className={({ isActive: act }) => `nav-child${act ? ' active' : ''}`}
              >
                <span className="nav-child-dot" aria-hidden="true" />
                <span>{ch.icon ? iconMap[ch.icon] : null}</span>
                <span>{ch.label}</span>
              </NavLink>
            ))}
          </div>
        )}
      </div>
    );
  }

  const activeItem = navItems.find((item) => {
    if (item.to && isActive(item.to)) return true;
    return item.children?.some((ch) => isActive(ch.to));
  });
  const activeChild = activeItem?.children?.find((ch) => isActive(ch.to));
  const topbarIcon = activeChild
    ? (activeChild.icon ? iconMap[activeChild.icon] : null) || (activeItem?.icon ? iconMap[activeItem.icon] : null)
    : (activeItem?.icon ? iconMap[activeItem.icon] : null);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="گندم دشت">
          <img src="/logo.png" alt="گندم دشت" />
        </a>
        <div className="sidebar-note">
          <span className="sidebar-note-mark" aria-hidden="true" />
          <span>سامانه مالی مزرعه</span>
        </div>
        {navItems.map(renderItem)}
      </aside>
      <div className="content">
        <header className="topbar">
          <div className="topbar-heading">
            {topbarIcon && <span style={{ display: 'inline-flex', color: 'var(--olive)' }}>{topbarIcon}</span>}
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
