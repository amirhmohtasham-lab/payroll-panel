// Sidebar navigation config — accountant/operator menus with sub-groups.

export interface NavChild {
  to: string;
  icon?: string;
  label: string;
}

export interface NavGroup {
  to?: string;
  icon?: string;
  label: string;
  children?: NavChild[];
}

export type NavItem = NavGroup;

export const ACCOUNTANT_NAV: NavItem[] = [
  { to: '/', icon: 'upload', label: 'بارگذاری اطلاعات جدید' },
  { to: '/archive', icon: 'folder', label: 'آرشیو اطلاعات' },
  {
    to: '/reports',
    icon: 'chart',
    label: 'گزارش‌ها',
    children: [{ to: '/chat', icon: 'robot', label: 'چت سفارش گزارش' }],
  },
  {
    icon: 'farm',
    label: 'مزرعه',
    children: [
      { to: '/reports?tab=payroll', icon: 'chart', label: 'مالی' },
      { to: '/reports?tab=fertilizer', icon: 'beaker', label: 'عملیاتی' },
    ],
  },
  {
    icon: 'leaf',
    label: 'گلخانه',
    children: [
      { to: '/greenhouse', icon: 'leaf', label: 'گلخانه هیدروپونیک' },
      { to: '/greenhouse/soil', icon: 'farm', label: 'گلخانه خاکی' },
    ],
  },
  { to: '/users', icon: 'user', label: 'کاربران' },
];

export const OPERATOR_NAV: NavItem[] = [{ to: '/operator', icon: 'upload', label: 'بارگذاری' }];
