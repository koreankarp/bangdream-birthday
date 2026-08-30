import { useEffect, useRef } from 'react';
import BirthdayPass from './BirthdayPass';
import type { Ticket } from '../types';

/**
 * 티켓을 누르면 그 캐릭터의 패스 카드를 띄우는 모달.
 *
 * 네이티브 <dialog> 의 showModal() 을 쓰면 Esc 닫기, 포커스 가두기, 스크롤 잠금,
 * 배경 inert 처리를 브라우저가 해준다. 직접 구현하면 놓치기 쉬운 부분들이다.
 */
export default function PassDialog({
  ticket,
  onClose,
}: {
  ticket: Ticket | null;
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (ticket && !dialog.open) {
      dialog.showModal();
    } else if (!ticket && dialog.open) {
      dialog.close();
    }
  }, [ticket]);

  return (
    <dialog
      ref={dialogRef}
      className="pass-dialog"
      // Esc 로 닫혔을 때도 부모 상태를 맞춘다.
      onClose={onClose}
      // 배경(dialog 자신)을 눌렀을 때만 닫는다. 카드 내부 클릭은 통과시킨다.
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      {ticket && (
        <div className="pass-dialog__inner">
          <BirthdayPass ticket={ticket} />
          <button type="button" className="pass-dialog__close" onClick={onClose}>
            닫기
          </button>
        </div>
      )}
    </dialog>
  );
}
