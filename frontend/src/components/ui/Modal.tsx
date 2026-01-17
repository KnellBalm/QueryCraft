import React, { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import styles from './Modal.module.css';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  header?: React.ReactNode;
  body?: React.ReactNode;
  footer?: React.ReactNode;
  children?: React.ReactNode;
  closeOnBackdropClick?: boolean;
  showCloseButton?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const Modal = React.memo<ModalProps>(({
  isOpen,
  onClose,
  header,
  body,
  footer,
  children,
  closeOnBackdropClick = true,
  showCloseButton = true,
  size = 'md',
}) => {
  const handleEscapeKey = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  const handleBackdropClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnBackdropClick && event.target === event.currentTarget) {
      onClose();
    }
  }, [closeOnBackdropClick, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'hidden';

      return () => {
        document.removeEventListener('keydown', handleEscapeKey);
        document.body.style.overflow = '';
      };
    }
  }, [isOpen, handleEscapeKey]);

  if (!isOpen) return null;

  const hasSlots = header || body || footer;

  const modalClassNames = [
    styles.modal,
    styles[`size-${size}`],
    isOpen && styles.open,
  ].filter(Boolean).join(' ');

  const modalContent = (
    <div
      className={`${styles.backdrop} ${isOpen ? styles.backdropOpen : ''}`}
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div className={modalClassNames} role="dialog" aria-modal="true">
        {showCloseButton && (
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close modal"
          >
            <span className={styles.closeIcon}>×</span>
          </button>
        )}

        {hasSlots ? (
          <>
            {header && (
              <div className={styles.header}>
                {header}
              </div>
            )}
            {body && (
              <div className={styles.body}>
                {body}
              </div>
            )}
            {footer && (
              <div className={styles.footer}>
                {footer}
              </div>
            )}
          </>
        ) : (
          <div className={styles.content}>
            {children}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
});

Modal.displayName = 'Modal';

export default Modal;
