// frontend/src/components/SQLEditor.tsx
import Editor from '@monaco-editor/react';
import { useCallback, useRef } from 'react';

interface SQLEditorProps {
    value: string;
    onChange: (value: string) => void;
    onExecute?: () => void;
    height?: string;
}

export function SQLEditor({ value, onChange, onExecute, height = '200px' }: SQLEditorProps) {
    const editorRef = useRef<any>(null);

    const handleMount = useCallback((editor: any) => {
        editorRef.current = editor;

        // Ctrl/Cmd + Enter로 실행
        editor.addCommand(
            // Monaco.KeyMod.CtrlCmd | Monaco.KeyCode.Enter
            2048 | 3, // CtrlCmd + Enter
            () => {
                if (onExecute) onExecute();
            }
        );
    }, [onExecute]);

    return (
        <div className="sql-editor">
            <Editor
                height={height}
                defaultLanguage="sql"
                theme="vs-dark"
                value={value}
                onChange={(val) => onChange(val || '')}
                onMount={handleMount}
                options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: 'on',
                    padding: { top: 10, bottom: 10 },
                }}
            />
        </div>
    );
}
