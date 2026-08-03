// ─── Minimal SVG icon set (heroicons outline style) ───
// All icons: 20×20, stroke-width 1.5, no fill

import React from 'react';

type Props = { size?: number; className?: string; style?: React.CSSProperties };

function Icon({ children, size = 20, className, style }: Props & { children: React.ReactNode }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
    >
      {children}
    </svg>
  );
}

// ─── Utility to create icon components ───
function ic(paths: string[]) {
  return ({ size, className, style }: Props = {}) => (
    <Icon size={size} className={className} style={style}>
      {paths.map((d, i) => <path key={i} d={d} />)}
    </Icon>
  );
}

function icCircle(path: string) {
  return ({ size, className, style }: Props = {}) => (
    <Icon size={size} className={className} style={style}>
      <circle cx="12" cy="12" r="10" />
      <path d={path} />
    </Icon>
  );
}

export const ChartBar = ic([
  'M3 13h4v8H3z',
  'M10 9h4v12h-4z',
  'M17 5h4v16h-4z',
]);

export const ChartBarSquare = ic([
  'M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5Z',
  'M9 8h2v8H9Z',
  'M13 12h2v4h-2Z',
  'M17 10h2v6h-2Z',
]);

export const MapPin = ic([
  'M12 2a8 8 0 0 0-8 8c0 5.4 8 12 8 12s8-6.6 8-12a8 8 0 0 0-8-8Z',
  'M12 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z',
]);

export const CalendarDays = ic([
  'M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z',
  'M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01',
]);

export const Leaf = ic([
  'M12 2C9 2 5 5 5 10c0 4 3 7 7 9 4-2 7-5 7-9 0-5-4-8-7-8Z',
  'M12 21v-7',
]);

export const Wheat = ic([
  'M7 12l5-5 5 5M12 7v14',
  'M7 16l5-5 5 5M8 21l4-4 4 4',
  'M12 2v5',
]);

export const BarChart = ic([
  'M18 20V10M12 20V4M6 20v-6',
]);

export const Pin = icCircle('M12 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z');

export const ArrowPath = ic([
  'M21 12a9 9 0 1 1-3-6.7M21 3v6h-6',
]);

export const Hashtag = ic([
  'M10 3L8 21M16 3l-2 18M3 8h18M3 16h18',
]);

export const Cog6Tooth = ic([
  'M12 6V4m0 2a2 2 0 0 1 2 2v.5M12 6a2 2 0 0 0-2 2v.5m4 0a2 2 0 0 1 2 2v.5M10 8.5a2 2 0 0 0-2 2v.5M14 12.5a2 2 0 0 0 2 2v.5m-4-2.5a2 2 0 0 1-2 2v.5m4 0a2 2 0 0 1-2 2v1m-2-3a2 2 0 0 0-2 2v1m0-3a2 2 0 0 0-2-2v-.5m4 3a2 2 0 0 0 2-2v-.5m-4 2.5h4',
]);

export const Trash = ic([
  'M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6',
]);

export const Upload = ic([
  'M12 3v12m0-12l-4 4m4-4l4 4M3 15v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2',
]);

export const Download = ic([
  'M12 21V9m0 12l-4-4m4 4l4-4M3 15v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2',
]);

export const Search = ic([
  'M21 21l-4.3-4.3M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z',
]);

export const User = ic([
  'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
]);

export const UserCircle = ic([
  'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z',
  'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z',
  'M4.2 18.4A8 8 0 0 1 12 14a8 8 0 0 1 7.8 4.4',
]);

export const ArchiveBox = ic([
  'M3 6h18M4 6v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6M9 12h6',
  'M3 4h18v3H3z',
]);

export const FolderOpen = ic([
  'M2 5a2 2 0 0 1 2-2h6l2 2h6a2 2 0 0 1 2 2v1H4V5Z',
  'M4 11h16l-2 8H6l-2-8Z',
]);

export const CheckCircle = icCircle('M9 12l2 2 4-4');

export const XCircle = icCircle('M15 9l-6 6m0-6l6 6');

export const ExclamationTriangle = ic([
  'M12 9v3m0 4h.01M10.3 3.7l-8.5 15a1.5 1.5 0 0 0 1.3 2.3h17a1.5 1.5 0 0 0 1.3-2.3l-8.4-15a1.5 1.5 0 0 0-2.7 0Z',
]);

export const PaperClip = ic([
  'M18.4 5.6a2 2 0 0 1 0 2.8L8.7 18A4 4 0 0 1 3 12.3L12.4 3a2 2 0 1 1 2.8 2.8l-9 9',
]);

export const Check = ic([
  'M5 13l4 4L19 7',
]);

export const Close = ic([
  'M6 6l12 12M18 6L6 18',
]);

export const Photo = ic([
  'M4 16l4-4 4 4 4-4 4 4M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z',
]);

export const Plus = ic([
  'M12 5v14m-7 0h14',
]);

export const Minus = ic([
  'M5 12h14',
]);

export const ChevronDown = ic([
  'M6 9l6 6 6-6',
]);

export const ChevronUp = ic([
  'M18 15l-6-6-6 6',
]);

export const ChevronLeft = ic([
  'M15 6l-6 6 6 6',
]);

export const ChevronRight = ic([
  'M9 6l6 6-6 6',
]);

export const Filter = ic([
  'M3 6h18M6 12h12M10 18h4',
]);

export const Refresh = ic([
  'M4 12a8 8 0 0 1 8-8 8 8 0 0 1 7.4 5M20 12a8 8 0 0 1-8 8 8 8 0 0 1-7.4-5M3 3v4h4M21 21v-4h-4',
]);

export const Export = ic([
  'M12 3v12m0-12l-3 3m3-3l3 3M3 15v2a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2',
]);

export const LockClosed = ic([
  'M8 11V7a4 4 0 0 1 8 0v4M5 11h14a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2Z',
]);

export const ChatBubble = ic([
  'M12 20c-4.4 0-8-3.1-8-7s3.6-7 8-7 8 3.1 8 7-3.6 7-8 7Z',
  'M8 10h8M8 14h5',
]);

export const Bolt = ic([
  'M13 2L3 14h7l-1 8 10-12h-7l1-8Z',
]);

export const Clipboard = ic([
  'M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 12l2 2 4-4',
]);

export const Menu = ic([
  'M3 6h18M3 12h18M3 18h18',
]);

export const Home = ic([
  'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 0 0 1 1h3m4 0a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1V10l-2-2',
]);

export const Info = icCircle('M12 8v4m0 4h.01');

export const WarningTriangle = ic([
  'M12 9v3m0 4h.01M10.3 3.7l-8.5 15a1.5 1.5 0 0 0 1.3 2.3h17a1.5 1.5 0 0 0 1.3-2.3l-8.4-15a1.5 1.5 0 0 0-2.7 0Z',
]);

export const Robot = ic([
  'M12 2a3 3 0 0 0-3 3v1h6V5a3 3 0 0 0-3-3Z',
  'M5 12h14M5 12a3 3 0 0 0-3 3v3a3 3 0 0 0 3 3h14a3 3 0 0 0 3-3v-3a3 3 0 0 0-3-3M5 12V6h14v6',
]);

export const Beaker = ic([
  'M7 3h10M9 3v5l-4 9a2 2 0 0 0 1.5 3h11a2 2 0 0 0 1.5-3l-4-9V3M8 16h8',
]);

export const Trophy = ic([
  'M6 3h12v4a6 6 0 0 1-12 0V3Z',
  'M4 7a4 4 0 0 0 4 4M20 7a4 4 0 0 1-4 4',
  'M12 11v2',
]);

export const PlusCircle = icCircle('M12 8v8m-4-4h8');

export const Eye = ic([
  'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z',
  'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z',
]);

export const DocumentText = ic([
  'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z',
  'M8 13h8M8 16h8M14 2v6h6',
]);


// ─── Redesigned icons (custom Illustrator designs) ───


export const NavArchive = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M20.25,7.5l-.62,10.63c-.07,1.19-1.06,2.12-2.25,2.12H6.62c-1.19,0-2.18-.93-2.25-2.12l-.62-10.63M10,11.25h4M3.38,7.5h17.25c.62,0,1.12-.5,1.12-1.12v-1.5c0-.62-.5-1.12-1.12-1.12H3.38c-.62,0-1.12.5-1.12,1.12v1.5c0,.62.5,1.12,1.12,1.12Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const NavChat = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3,13.12c0-.62.5-1.12,1.12-1.12h2.25c.62,0,1.12.5,1.12,1.12v6.75c0,.62-.5,1.12-1.12,1.12h-2.25c-.62,0-1.12-.5-1.12-1.12h0v-6.75ZM9.75,8.62c0-.62.5-1.12,1.12-1.12h2.25c.62,0,1.12.5,1.12,1.12v11.25c0,.62-.5,1.12-1.12,1.12h-2.25c-.62,0-1.12-.5-1.12-1.12v-11.25ZM16.5,4.12c0-.62.5-1.12,1.12-1.12h2.25c.62,0,1.12.5,1.12,1.12v15.75c0,.62-.5,1.12-1.12,1.12h-2.25c-.62,0-1.12-.5-1.12-1.12V4.12Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const NavFertilizer = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3.06,5.82h8.18M4.7,5.82v4.09l-3.27,7.36c-.46.78-.2,1.78.58,2.24.2.12.42.19.64.21h8.99c.9-.1,1.54-.91,1.44-1.81-.03-.23-.1-.45-.21-.64l-3.27-7.36v-4.09M3.88,16.45h6.54" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M23.14,6.58c-.06-.72-.65-1.25-1.38-1.25h-7.58c-.71.01-1.32.67-1.33,1.38v11.94c-.01.81.52,1.57,1.39,1.57h2.33c.78,0,1.37-.69,1.37-1.46v-3.98s2.94-.01,2.94-.01c.72,0,1.3-.62,1.3-1.33v-1.2c.01-.72-.49-1.3-1.2-1.38h-3.03v-1.51h3.96c.7-.08,1.25-.58,1.26-1.3.01-.49.02-.99-.01-1.47ZM22.36,8.04c0,.31-.3.5-.59.5h-4.27c-.14,0-.36.15-.36.3v2.48c-.01.15.19.32.36.32h3.33c.25,0,.53.16.53.46v1.28c.02.31-.19.6-.54.6h-3.27c-.16,0-.4.1-.4.3v4.47c-.01.36-.3.68-.65.68h-2.17c-.32,0-.69-.25-.69-.62V6.7c0-.37.36-.59.68-.59h7.49c.31,0,.55.28.55.57v1.35Z" fill="currentColor" stroke="currentColor" strokeWidth={0.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const NavGreenhouse = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3.28,9.01V2.01" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M7.73,9.01V2.01" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M3.44,5.51h4.29" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M10.05,5.51v-3.5" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M14.5,9.01V2.01" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M17.17,9.01V2.01" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M10.21,5.51h4.29" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M23.2,17.01c-.14-3.67-3.11-6.6-6.78-6.6H7.81c-3.68-.03-6.8,2.86-6.91,6.58v5.16h22.1c.14,0,.23-.14.23-.28l-.03-4.87ZM3.01,12.93l2.26,2.9H1.48c.25-1.08.76-2.06,1.53-2.9ZM1.3,17.09l.08-.84h3.89s-3.95,5.04-3.95,5.04l-.03-4.2ZM1.55,21.73l3.95-5.02v5.01s-3.95.01-3.95.01ZM9.7,21.73h-3.75l.03-6.03c0-1.01.95-1.67,1.85-1.67.97,0,1.78.73,1.88,1.71v5.99ZM7.88,13.6c-1.1-.03-2.06.68-2.35,1.85l-2.22-2.83c1.39-1.35,3.33-1.97,5.29-1.75,1.41.15,2.68.75,3.75,1.75l-2.22,2.82c-.3-1.08-1.16-1.82-2.25-1.84ZM12.66,12.93c.73.84,1.24,1.74,1.52,2.9h-3.8l2.28-2.9ZM10.14,21.75v-5.05s3.96,5.02,3.96,5.02l-3.96.03ZM14.33,21.29l-3.95-5.02h3.88s.08.72.08.72v4.31ZM10.38,10.84c3.09-.17,5.87,1.89,6.61,4.97l-2.36.04c-.5-2.26-2.03-4.09-4.25-5.01ZM17.17,21.73h-2.4v-4.31s-.06-1.17-.06-1.17h2.36l.1.95v4.53ZM15.79,12.65c-.7-.81-1.53-1.32-2.55-1.81,3.13-.15,5.87,1.99,6.57,5h-2.36c-.28-1.19-.8-2.3-1.66-3.19ZM17.58,21.76l-.07-5.51,2.44-.03.07,5.51-2.44.03ZM16.04,10.84c3.09-.15,5.85,1.92,6.57,4.97l-2.36.03c-.48-2.26-2-4.04-4.21-5ZM20.37,21.75l-.03-5.49h2.43s.03,5.48.03,5.48h-2.43Z" fill="currentColor" stroke="currentColor" strokeWidth={0.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M17.17,9.01c2.78,0,5.04-1.57,5.04-3.5s-2.26-3.5-5.04-3.5" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const DashFertilizer = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3.06,5.82h8.18M4.7,5.82v4.09l-3.27,7.36c-.46.78-.2,1.78.58,2.24.2.12.42.19.64.21h8.99c.9-.1,1.54-.91,1.44-1.81-.03-.23-.1-.45-.21-.64l-3.27-7.36v-4.09M3.88,16.45h6.54" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M23.14,6.58c-.06-.72-.65-1.25-1.38-1.25h-7.58c-.71.01-1.32.67-1.33,1.38v11.94c-.01.81.52,1.57,1.39,1.57h2.33c.78,0,1.37-.69,1.37-1.46v-3.98s2.94-.01,2.94-.01c.72,0,1.3-.62,1.3-1.33v-1.2c.01-.72-.49-1.3-1.2-1.38h-3.03v-1.51h3.96c.7-.08,1.25-.58,1.26-1.3.01-.49.02-.99-.01-1.47ZM22.36,8.04c0,.31-.3.5-.59.5h-4.27c-.14,0-.36.15-.36.3v2.48c-.01.15.19.32.36.32h3.33c.25,0,.53.16.53.46v1.28c.02.31-.19.6-.54.6h-3.27c-.16,0-.4.1-.4.3v4.47c-.01.36-.3.68-.65.68h-2.17c-.32,0-.69-.25-.69-.62V6.7c0-.37.36-.59.68-.59h7.49c.31,0,.55.28.55.57v1.35Z" fill="currentColor" stroke="currentColor" strokeWidth={0.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const DashWorker = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M16.87,13.93l-1.89-.4c-.46-.1-.83-.32-1.08-.74,1.2-.67,1.96-1.95,1.97-3.35v-1.13c1.07.1,1.86-.72,1.84-1.75-.01-.46-.29-.87-.8-.87h-.55c.12-2.53-1.88-4.62-4.38-4.61-2.48.02-4.46,2.1-4.33,4.6h-.51c-.53,0-.83.4-.84.89-.03,1.04.8,1.84,1.84,1.74v1.18c0,1.37.76,2.62,1.98,3.3-.2.27-.46.59-.81.66l-2.18.49c-1.64.36-2.93,1.72-2.94,3.44v5.16c-.01.19.12.37.35.37h15c.16,0,.29-.22.29-.32v-5.06c0-1.78-1.24-3.23-2.96-3.6ZM14.69,14.17c-.12.85-.38,1.58-.58,2.47l-1.37-.72c.99-.16,1.6-.78,1.95-1.75ZM10.6,2.09v2.69c.04.2.17.33.35.34.13.01.37-.12.37-.3V1.86c.47-.08.9-.08,1.36,0v2.91c0,.19.18.32.32.34.19.02.4-.12.4-.34v-2.69c1.42.59,2.34,2.01,2.23,3.6h-7.25c-.11-1.53.74-2.97,2.22-3.6ZM7.81,7.59c-.58,0-.9-.71-.75-1.18h9.88c.16.47-.16,1.18-.74,1.18H7.81ZM8.86,9.56v-1.25s6.29,0,6.29,0v1.24c-.07,1.71-1.48,3.01-3.12,3.02-1.68.02-3.09-1.29-3.17-3.01ZM10.76,13.1c.79.26,1.65.28,2.45,0,.21.31.44.57.74.81-.09.68-.65,1.22-1.36,1.29h-1.22c-.69-.08-1.24-.6-1.33-1.29.28-.24.52-.48.72-.81ZM11.25,15.92l-1.34.72c-.21-.82-.46-1.6-.6-2.47.36.93.9,1.56,1.94,1.75ZM7.29,22.19h-2.39s0-4.77,0-4.77c.04-1.38,1.03-2.52,2.39-2.78v7.55ZM16,22.19h-7.99v-7.71l.57-.13.74,2.88c.05.22.28.38.5.26l1.82-.96v1.88s-1.17,0-1.17,0c-.21,0-.36.15-.38.33s.1.39.32.39h3.13c.22,0,.37-.15.38-.35,0-.16-.13-.36-.34-.36h-1.22s.01-1.89.01-1.89l1.79.95c.07.04.25.05.33.02.07-.04.17-.16.2-.26l.74-2.89.57.13v7.71ZM19.12,22.19h-2.4v-7.55c1.34.25,2.31,1.37,2.4,2.74v4.81Z" fill="currentColor" stroke="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const RepExportCsv = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3,15v2c0,1.1.9,2,2,2h14c1.1,0,2-.9,2-2v-2" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const RepMonthlyTrend = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3,5c0-1.1.9-2,2-2h14c1.1,0,2,.9,2,2v14c0,1.1-.9,2-2,2H5c-1.1,0-2-.9-2-2V5Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M7,8h2v8h-2v-8Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M11,12h2v4h-2v-4Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M15,10h2v6h-2v-6Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const RepSettings = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M10.5,6h9.75M10.5,6c0,.83-.67,1.5-1.5,1.5s-1.5-.67-1.5-1.5M10.5,6c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5,1.5M3.75,6h3.75M10.5,18h9.75M10.5,18c0,.83-.67,1.5-1.5,1.5s-1.5-.67-1.5-1.5M10.5,18c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5,1.5M3.75,18h3.75M16.5,12h3.75M16.5,12c0,.83-.67,1.5-1.5,1.5s-1.5-.67-1.5-1.5M16.5,12c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5,1.5M3.75,12h9.75" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const RepTop5 = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M12.54,13.62l3.25,3.25,6.49-6.49" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M7.34,20.39c-.75,0-1.42-.15-2.01-.44s-1.07-.7-1.42-1.21-.55-1.09-.57-1.74h1.58c.03.38.16.71.39,1.01s.51.53.87.7.75.25,1.18.25c.51,0,.97-.12,1.38-.36s.72-.57.95-.99.34-.9.34-1.44-.12-1.04-.36-1.47-.57-.78-.98-1.02-.89-.37-1.43-.37c-.39,0-.79.06-1.2.19s-.73.29-.99.48l-1.53-.19.75-6.33h6.72v1.43h-5.35l-.44,3.73h.07c.26-.22.59-.4.99-.54s.82-.21,1.26-.21c.58,0,1.12.11,1.62.32s.92.51,1.29.9.65.84.85,1.36.3,1.09.3,1.71c0,.82-.18,1.55-.55,2.19s-.87,1.14-1.51,1.51-1.37.55-2.19.55Z" fill="none" stroke="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const RepWorker = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M16.87,13.93l-1.89-.4c-.46-.1-.83-.32-1.08-.74,1.2-.67,1.96-1.95,1.97-3.35v-1.13c1.07.1,1.86-.72,1.84-1.75-.01-.46-.29-.87-.8-.87h-.55c.12-2.53-1.88-4.62-4.38-4.61-2.48.02-4.46,2.1-4.33,4.6h-.51c-.53,0-.83.4-.84.89-.03,1.04.8,1.84,1.84,1.74v1.18c0,1.37.76,2.62,1.98,3.3-.2.27-.46.59-.81.66l-2.18.49c-1.64.36-2.93,1.72-2.94,3.44v5.16c-.01.19.12.37.35.37h15c.16,0,.29-.22.29-.32v-5.06c0-1.78-1.24-3.23-2.96-3.6ZM14.69,14.17c-.12.85-.38,1.58-.58,2.47l-1.37-.72c.99-.16,1.6-.78,1.95-1.75ZM10.6,2.09v2.69c.04.2.17.33.35.34.13.01.37-.12.37-.3V1.86c.47-.08.9-.08,1.36,0v2.91c0,.19.18.32.32.34.19.02.4-.12.4-.34v-2.69c1.42.59,2.34,2.01,2.23,3.6h-7.25c-.11-1.53.74-2.97,2.22-3.6ZM7.81,7.59c-.58,0-.9-.71-.75-1.18h9.88c.16.47-.16,1.18-.74,1.18H7.81ZM8.86,9.56v-1.25s6.29,0,6.29,0v1.24c-.07,1.71-1.48,3.01-3.12,3.02-1.68.02-3.09-1.29-3.17-3.01ZM10.76,13.1c.79.26,1.65.28,2.45,0,.21.31.44.57.74.81-.09.68-.65,1.22-1.36,1.29h-1.22c-.69-.08-1.24-.6-1.33-1.29.28-.24.52-.48.72-.81ZM11.25,15.92l-1.34.72c-.21-.82-.46-1.6-.6-2.47.36.93.9,1.56,1.94,1.75ZM7.29,22.19h-2.39s0-4.77,0-4.77c.04-1.38,1.03-2.52,2.39-2.78v7.55ZM16,22.19h-7.99v-7.71l.57-.13.74,2.88c.05.22.28.38.5.26l1.82-.96v1.88s-1.17,0-1.17,0c-.21,0-.36.15-.38.33s.1.39.32.39h3.13c.22,0,.37-.15.38-.35,0-.16-.13-.36-.34-.36h-1.22s.01-1.89.01-1.89l1.79.95c.07.04.25.05.33.02.07-.04.17-.16.2-.26l.74-2.89.57.13v7.71ZM19.12,22.19h-2.4v-7.55c1.34.25,2.31,1.37,2.4,2.74v4.81Z" fill="currentColor" stroke="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const ArchFertilizer = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M2.87,5.05h8.18M4.51,5.05v4.09l-3.27,7.36c-.46.78-.2,1.78.58,2.24.2.12.42.19.64.21h8.99c.9-.1,1.54-.91,1.44-1.81-.03-.23-.1-.45-.21-.64l-3.27-7.36v-4.09M3.69,15.68h6.54" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    <path d="M22.95,5.81c-.06-.72-.65-1.25-1.38-1.25h-7.58c-.71.01-1.32.67-1.33,1.38v11.94c-.01.81.52,1.57,1.39,1.57h2.33c.78,0,1.37-.69,1.37-1.46v-3.98h2.94c.72-.01,1.3-.63,1.3-1.34v-1.2c.01-.72-.49-1.3-1.2-1.38h-3.03v-1.51h3.96c.7-.08,1.25-.58,1.26-1.3.01-.49.02-.99-.01-1.47h-.02ZM22.17,7.27c0,.31-.3.5-.59.5h-4.27c-.14,0-.36.15-.36.3v2.48c-.01.15.19.32.36.32h3.33c.25,0,.53.16.53.46v1.28c.02.31-.19.6-.54.6h-3.27c-.16,0-.4.1-.4.3v4.47c-.01.36-.3.68-.65.68h-2.17c-.32,0-.69-.25-.69-.62V5.93c0-.37.36-.59.68-.59h7.49c.31,0,.55.28.55.57v1.35h0Z" fill="currentColor" stroke="currentColor" strokeWidth={0.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const ArchFolder = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M20.24,7.49l-.62,10.63c-.07,1.19-1.06,2.12-2.25,2.12H6.61c-1.19,0-2.18-.93-2.25-2.12l-.62-10.63M9.99,11.24h4M3.37,7.49h17.25c.62,0,1.12-.5,1.12-1.12v-1.5c0-.62-.5-1.12-1.12-1.12H3.37c-.62,0-1.12.5-1.12,1.12v1.5c0,.62.5,1.12,1.12,1.12Z" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const ChatRobot = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M20.5,8.96c.88.28,1.5,1.13,1.5,2.1v4.29c0,1.14-.85,2.1-1.98,2.19-.34.03-.68.05-1.02.07v3.09l-3-3c-1.35,0-2.69-.06-4.02-.16-.29-.02-.57-.11-.82-.24M20.5,8.96c-.15-.05-.31-.08-.48-.1-2.68-.22-5.37-.22-8.05,0-1.13.09-1.98,1.06-1.98,2.19v4.29c0,.84.46,1.58,1.15,1.95M20.5,8.96v-1.87c0-1.62-1.15-3.03-2.76-3.23-2.07-.27-4.15-.4-6.24-.4-2.11,0-4.2.14-6.24.4-1.61.21-2.76,1.61-2.76,3.24v6.23c0,1.62,1.15,3.03,2.76,3.23.58.08,1.16.14,1.74.19v4.71l4.16-4.16" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const GhDownloadZip = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M3,15.7v2c0,1.1.9,2,2,2h14c1.1,0,2-.9,2-2v-2" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const GhLeaf = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M23.14,12.73c-.14-3.67-3.11-6.6-6.78-6.6H7.75c-3.68-.03-6.8,2.86-6.91,6.58v5.16h22.1c.14,0,.23-.14.23-.28l-.03-4.87h0ZM2.95,8.65l2.26,2.9H1.42c.25-1.08.76-2.06,1.53-2.9ZM1.24,12.81l.08-.84h3.89l-3.95,5.04-.03-4.2h0ZM1.49,17.45l3.95-5.02v5.01H1.49ZM9.63,17.45h-3.75l.03-6.03c0-1.01.95-1.67,1.85-1.67.97,0,1.78.73,1.88,1.71v5.99h-.01ZM7.82,9.32c-1.1-.03-2.06.68-2.35,1.85l-2.22-2.83c1.39-1.35,3.33-1.97,5.29-1.75,1.41.15,2.68.75,3.75,1.75l-2.22,2.82c-.3-1.08-1.16-1.82-2.25-1.84ZM12.6,8.65c.73.84,1.24,1.74,1.52,2.9h-3.8l2.28-2.9ZM10.08,17.47v-5.05l3.96,5.02s-3.96.03-3.96.03ZM14.27,17.01l-3.95-5.02h3.88l.08.72v4.31h-.01ZM10.32,6.56c3.09-.17,5.87,1.89,6.61,4.97l-2.36.04c-.5-2.26-2.03-4.09-4.25-5.01ZM17.11,17.45h-2.4v-4.31l-.06-1.17h2.36l.1.95s0,4.53,0,4.53ZM15.73,8.37c-.7-.81-1.53-1.32-2.55-1.81,3.13-.15,5.87,1.99,6.57,5h-2.36c-.28-1.19-.8-2.3-1.66-3.19ZM17.52,17.48l-.07-5.51,2.44-.03.07,5.51-2.44.03ZM15.98,6.56c3.09-.15,5.85,1.92,6.57,4.97l-2.36.03c-.48-2.26-2-4.04-4.21-5ZM20.31,17.47l-.03-5.49h2.43l.03,5.48h-2.43Z" fill="currentColor" stroke="currentColor" strokeWidth={0.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const GhSettings = ({ size = 20, className, style }: Props) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    className={className}
    style={{ display: 'inline-block', verticalAlign: 'middle', ...style }}
  >
    <path d="M10.5,6.44h9.75M10.5,6.44c0,.83-.67,1.5-1.5,1.5s-1.5-.67-1.5-1.5M10.5,6.44c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5,1.5M3.75,6.44h3.75M10.5,18.44h9.75M10.5,18.44c0,.83-.67,1.5-1.5,1.5s-1.5-.67-1.5-1.5M10.5,18.44c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5,1.5M3.75,18.44h3.75M16.5,12.44h3.75M16.5,12.44c0,.83-.67,1.5-1.5,1.5s-1.5-.67-1.5-1.5M16.5,12.44c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5,1.5M3.75,12.44h9.75" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
