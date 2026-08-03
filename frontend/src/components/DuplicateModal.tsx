// Duplicate-upload modal — lets the user overwrite or cancel.

import type { DuplicateInfo } from '../api/types';

export function DuplicateModal({
  info,
  onConfirm,
  onCancel,
}: {
  info: DuplicateInfo;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="modal-backdrop">
      <div className="modal-box">
        <h3 style={{ marginBottom: '.5rem' }}> فایل تکراری</h3>
        <p style={{ color: 'var(--text-sec)', fontSize: '.9rem' }}>
          برای «{info.existing.month_label || info.existing.month_key}» قبلاً فایل ثبت شده. جایگزین
          شود؟
        </p>
        <p style={{ display: 'flex', gap: '.5rem', marginTop: '1rem' }}>
          <button className="primary" onClick={onConfirm}>
            جایگزین شود
          </button>
          <button className="secondary" onClick={onCancel}>
            انصراف
          </button>
        </p>
      </div>
    </div>
  );
}
