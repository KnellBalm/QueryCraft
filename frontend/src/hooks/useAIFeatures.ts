// frontend/src/hooks/useAIFeatures.ts
import { useState, useCallback } from 'react';
import { sqlApi } from '../api/client';
import { analytics } from '../services/analytics';
import type { Problem, SQLExecuteResponse } from '../types';

interface AIHelpResult {
    type: string;
    content: string;
}

interface InsightData {
    key_findings: string[];
    insights: string[];
    action_items: string[];
    suggested_queries: string[];
    report_markdown: string;
}

interface CompletedStatus {
    [problemId: string]: { is_correct: boolean; submitted_at: string };
}

interface UseAIFeaturesOptions {
    selectedProblem: Problem | undefined;
    sql: string;
    result: SQLExecuteResponse | null;
    dataType: string;
    completedStatus?: CompletedStatus;
}

interface UseAIFeaturesReturn {
    // Insight
    insightData: InsightData | null;
    showInsightModal: boolean;
    insightLoading: boolean;
    handleInsight: () => Promise<void>;
    setShowInsightModal: (show: boolean) => void;

    // Translation
    translateQuery: string;
    translating: boolean;
    setTranslateQuery: (query: string) => void;
    handleTranslate: () => Promise<void>;

    // AI Help
    aiHelpResult: AIHelpResult | null;
    aiHelpLoading: boolean;
    aiHelpUsed: { [problemId: string]: boolean };
    showAiHelpMenu: boolean;
    setShowAiHelpMenu: (show: boolean) => void;
    handleAiHelp: (helpType: 'hint' | 'solution') => Promise<void>;
}

/**
 * Custom hook for managing AI features in Workspace
 * Extracts AI-related state and handlers: Insight, Text-to-SQL, AI Help
 */
export function useAIFeatures({
    selectedProblem,
    sql,
    result,
    dataType,
    completedStatus = {}
}: UseAIFeaturesOptions): UseAIFeaturesReturn {
    // Insight state
    const [insightData, setInsightData] = useState<InsightData | null>(null);
    const [showInsightModal, setShowInsightModal] = useState(false);
    const [insightLoading, setInsightLoading] = useState(false);

    // Translation state
    const [translateQuery, setTranslateQuery] = useState('');
    const [translating, setTranslating] = useState(false);

    // AI Help state
    const [aiHelpUsed, setAiHelpUsed] = useState<{ [problemId: string]: boolean }>({});
    const [aiHelpResult, setAiHelpResult] = useState<AIHelpResult | null>(null);
    const [aiHelpLoading, setAiHelpLoading] = useState(false);
    const [showAiHelpMenu, setShowAiHelpMenu] = useState(false);

    /**
     * Request AI insights for the current query result
     */
    const handleInsight = useCallback(async () => {
        if (!result?.data || !selectedProblem || !result.success) return;

        setInsightLoading(true);
        setInsightData(null);

        analytics.aiInsightRequested(selectedProblem.problem_id, {
            dataType: dataType,
            resultCount: result.data.length
        });

        try {
            const res = await sqlApi.insight(selectedProblem.problem_id, sql, result.data, dataType);
            setInsightData(res.data);
            setShowInsightModal(true);
        } catch (error: any) {
            console.error('Failed to get AI insight:', error);
            // Show error message in modal
            setInsightData({
                key_findings: [],
                insights: [],
                action_items: [],
                suggested_queries: [],
                report_markdown: `# 오류\n\n인사이트 생성 실패: ${error.message}`
            });
            setShowInsightModal(true);
        } finally {
            setInsightLoading(false);
        }
    }, [result, selectedProblem, sql, dataType]);

    /**
     * Translate natural language query to SQL
     */
    const handleTranslate = useCallback(async () => {
        if (!translateQuery.trim()) return;

        setTranslating(true);

        analytics.textToSQLRequested(translateQuery, {
            problemId: selectedProblem?.problem_id,
            dataType: dataType
        });

        try {
            const res = await sqlApi.translate(translateQuery, dataType);
            // Note: The parent component should handle setSql
            // We can't do it here without exposing setSql callback
            return res.data.sql;
        } catch (error: any) {
            console.error('Translation failed:', error);
            throw error;
        } finally {
            setTranslating(false);
        }
    }, [translateQuery, selectedProblem?.problem_id, dataType]);

    /**
     * Request AI help (hint or solution) for the current problem
     * Can only be used once per problem
     */
    const handleAiHelp = useCallback(async (helpType: 'hint' | 'solution') => {
        if (!selectedProblem) return;
        if (aiHelpUsed[selectedProblem.problem_id]) return; // Already used

        setAiHelpLoading(true);
        setShowAiHelpMenu(false);
        setAiHelpResult(null);

        // Calculate attempt count from completion status
        const attemptCount = completedStatus[selectedProblem.problem_id] ? 1 : 0;

        try {
            const res = await sqlApi.aiHelp(
                selectedProblem.problem_id,
                helpType,
                sql,
                attemptCount,
                dataType
            );
            setAiHelpResult(res.data);

            // Mark as used and save to localStorage
            const newUsed = { ...aiHelpUsed, [selectedProblem.problem_id]: true };
            setAiHelpUsed(newUsed);
            localStorage.setItem(`ai_help_used_${dataType}`, JSON.stringify(newUsed));

            analytics.aiHelpRequested(selectedProblem.problem_id, helpType, {
                difficulty: selectedProblem.difficulty,
                dataType: dataType,
                attemptsBefore: attemptCount
            });
        } catch (error: any) {
            setAiHelpResult({
                type: 'error',
                content: `AI 도움 요청 실패: ${error.message}`
            });
        } finally {
            setAiHelpLoading(false);
        }
    }, [selectedProblem, aiHelpUsed, sql, completedStatus, dataType]);

    return {
        // Insight
        insightData,
        showInsightModal,
        insightLoading,
        handleInsight,
        setShowInsightModal,

        // Translation
        translateQuery,
        translating,
        setTranslateQuery,
        handleTranslate,

        // AI Help
        aiHelpResult,
        aiHelpLoading,
        aiHelpUsed,
        showAiHelpMenu,
        setShowAiHelpMenu,
        handleAiHelp
    };
}
