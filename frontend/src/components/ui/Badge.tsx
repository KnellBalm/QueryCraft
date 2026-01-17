import React from 'react';
import styles from './Badge.module.css';

export type BadgeVariant = 'default' | 'success' | 'error' | 'warning' | 'info';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  onRemove?: () => void;
  children?: React.ReactNode;
}

const Badge = React.memo<BadgeProps>(({
  variant = 'default',
  size = 'md',
  onRemove,
  children,
  className,
  ...props
}) => {
  const classNames = [
    styles.badge,
    styles[variant],
    styles[size],
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={classNames} {...props}>
      <span className={styles.content}>{children}</span>
      {onRemove && (
        <button
          type="button"
          className={styles.removeButton}
          onClick={onRemove}
          aria-label="Remove"
        >
          <span className={styles.removeIcon}>×</span>
        </button>
      )}
    </span>
  );
});

Badge.displayName = 'Badge';

export default Badge;
