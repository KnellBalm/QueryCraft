import React from 'react';
import styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';
export type IconPosition = 'left' | 'right';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: IconPosition;
  children?: React.ReactNode;
}

const Button = React.memo<ButtonProps>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'left',
  children,
  className,
  ...props
}) => {
  const classNames = [
    styles.button,
    styles[variant],
    styles[size],
    loading && styles.loading,
    disabled && styles.disabled,
    className,
  ].filter(Boolean).join(' ');

  const showIcon = icon && !loading;
  const showSpinner = loading;

  return (
    <button
      className={classNames}
      disabled={disabled || loading}
      {...props}
    >
      {showSpinner && (
        <span className={styles.spinner}>
          <span className={styles.spinnerCircle} />
        </span>
      )}

      {!loading && iconPosition === 'left' && showIcon && (
        <span className={styles.iconLeft}>{icon}</span>
      )}

      {children && <span className={styles.content}>{children}</span>}

      {!loading && iconPosition === 'right' && showIcon && (
        <span className={styles.iconRight}>{icon}</span>
      )}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;
