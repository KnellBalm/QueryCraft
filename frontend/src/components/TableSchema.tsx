// frontend/src/components/TableSchema.tsx
import type { TableSchema as Schema } from '../types';
import './TableSchema.css';

interface TableSchemaProps {
    tables: Schema[];
}

export function TableSchema({ tables }: TableSchemaProps) {
    if (!tables.length) {
        return <div className="schema-empty">테이블이 없습니다.</div>;
    }

    return (
        <div className="schema-container">
            <h3>📋 테이블 구조</h3>
            {tables.map((table) => (
                <details key={table.table_name} className="schema-table">
                    <summary>
                        <span className="table-icon">📁</span>
                        <span className="table-name">{table.table_name}</span>
                        {table.row_count !== undefined && (
                            <span className="row-count">{table.row_count.toLocaleString()} rows</span>
                        )}
                    </summary>
                    <div className="columns">
                        {table.columns.map((col) => (
                            <div key={col.column_name} className="column">
                                <code>{col.column_name}</code>
                                <span className="type">{col.data_type}</span>
                            </div>
                        ))}
                    </div>
                </details>
            ))}
        </div>
    );
}
