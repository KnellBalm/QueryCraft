import React from 'react';
import styles from './Card.module.css';

export type CardPadding = 'none' | 'sm' | 'md' | 'lg';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  header?: React.ReactNode;
  body?: React.ReactNode;
  footer?: React.ReactNode;
  children?: React.ReactNode;
  border?: boolean;
  hover?: boolean;
  padding?: CardPadding;
}

const Card = React.memo<CardProps>(({
  header,
  body,
  footer,
  children,
  border = true,
  hover = false,
  padding = 'md',
  className,
  ...props
}) => {
  const classNames = [
    styles.card,
    border && styles.border,
    hover && styles.hover,
    styles[`padding-${padding}`],
    className,
  ].filter(Boolean).join(' ');

  const hasSlots = header || body || footer;

  return (
    <div className={classNames} {...props}>
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
        children
      )}
    </div>
  );
});

Card.displayName = 'Card';

export default Card;
