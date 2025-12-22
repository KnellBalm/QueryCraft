// frontend/src/components/ResultTable.tsx
import './ResultTable.css';

interface ResultTableProps {
    columns: string[];
    data: Record<string, any>[];
    executionTime?: number;
}

export function ResultTable({ columns, data, executionTime }: ResultTableProps) {
    if (!data.length) {
        return <div className="result-empty">결과가 없습니다.</div>;
    }

    return (
        <div className="result-container">
            <div className="result-header">
                <span className="result-count">{data.length} rows</span>
                {executionTime !== undefined && (
                    <span className="result-time">{executionTime.toFixed(0)}ms</span>
                )}
            </div>
            <div className="result-scroll">
                <table className="result-table">
                    <thead>
                        <tr>
                            {columns.map((col) => (
                                <th key={col}>{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row, i) => (
                            <tr key={i}>
                                {columns.map((col) => (
                                    <td key={col}>{formatValue(row[col])}</td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function formatValue(value: any): string {
    if (value === null || value === undefined) return 'NULL';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
}
