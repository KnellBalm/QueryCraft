import React from 'react';
import styles from './Input.module.css';

export type InputType = 'text' | 'email' | 'password' | 'number';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  type?: InputType;
  prefixIcon?: React.ReactNode;
  suffixIcon?: React.ReactNode;
}

const Input = React.memo<InputProps>(({
  label,
  error,
  type = 'text',
  prefixIcon,
  suffixIcon,
  disabled = false,
  className,
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const hasError = Boolean(error);

  const wrapperClassNames = [
    styles.wrapper,
    disabled && styles.disabled,
    className,
  ].filter(Boolean).join(' ');

  const inputContainerClassNames = [
    styles.inputContainer,
    hasError && styles.error,
    prefixIcon && styles.hasPrefix,
    suffixIcon && styles.hasSuffix,
  ].filter(Boolean).join(' ');

  return (
    <div className={wrapperClassNames}>
      {label && (
        <label htmlFor={inputId} className={styles.label}>
          {label}
        </label>
      )}

      <div className={inputContainerClassNames}>
        {prefixIcon && (
          <span className={styles.prefixIcon}>
            {prefixIcon}
          </span>
        )}

        <input
          id={inputId}
          type={type}
          className={styles.input}
          disabled={disabled}
          {...props}
        />

        {suffixIcon && (
          <span className={styles.suffixIcon}>
            {suffixIcon}
          </span>
        )}
      </div>

      {error && (
        <span className={styles.errorMessage}>
          {error}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
