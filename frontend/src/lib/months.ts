export const PERSIAN_MONTHS: [string, string][] = [
  ['01', 'فروردین'],
  ['02', 'اردیبهشت'],
  ['03', 'خرداد'],
  ['04', 'تیر'],
  ['05', 'مرداد'],
  ['06', 'شهریور'],
  ['07', 'مهر'],
  ['08', 'آبان'],
  ['09', 'آذر'],
  ['10', 'دی'],
  ['11', 'بهمن'],
  ['12', 'اسفند'],
];

export const CROPS = [
  'گوجه فرنگی',
  'گندم',
  'جو',
  'زیره',
  'نخود',
  'سیب زمینی',
  'زعفران',
  'فلفل دلمه‌ای',
  'پیاز',
  'سیر',
];

export function monthOptions(fromYear = 1403, toYear = 1407): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  for (let yr = fromYear; yr <= toYear; yr++) {
    for (const [num, name] of PERSIAN_MONTHS) {
      options.push({ value: `${yr}-${num}`, label: `${name} ${yr}` });
    }
  }
  return options;
}

export function formatNumber(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  const n = typeof value === 'number' ? value : parseFloat(value);
  return Number.isNaN(n) ? '' : n.toLocaleString('fa-IR');
}
