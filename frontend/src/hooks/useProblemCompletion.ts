// frontend/src/hooks/useProblemCompletion.ts
import { useCallback, useMemo, useReducer } from 'react';
import type { Problem } from '../types';

export interface CompletedStatus {
  [problemId: string]: {
    is_correct: boolean;
    submitted_at: string;
  };
}

interface State {
  problemIds: string;
  completedStatus: CompletedStatus;
}

type Action =
  | { type: 'UPDATE_COMPLETION'; problemId: string; isCorrect: boolean }
  | { type: 'SYNC_PROBLEMS'; problemIds: string; dataType: string };

/**
 * Load completion history from localStorage with problem ID validation.
 */
function loadCompletionFromStorage(
  dataType: string,
  currentProblemIds: string
): CompletedStatus {
  const savedKey = `completed_${dataType}`;
  const savedProblemIdsKey = `problem_ids_${dataType}`;
  const savedProblemIds = localStorage.getItem(savedProblemIdsKey);

  if (savedProblemIds !== currentProblemIds) {
    // New problem set - clear old completion history
    localStorage.removeItem(savedKey);
    localStorage.setItem(savedProblemIdsKey, currentProblemIds);
    return {};
  } else {
    // Same problem set - restore saved history
    const saved = localStorage.getItem(savedKey);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Invalid JSON - reset to empty
        return {};
      }
    }
    return {};
  }
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'UPDATE_COMPLETION': {
      const newStatus = {
        ...state.completedStatus,
        [action.problemId]: {
          is_correct: action.isCorrect,
          submitted_at: new Date().toISOString(),
        },
      };
      return {
        ...state,
        completedStatus: newStatus,
      };
    }
    case 'SYNC_PROBLEMS': {
      if (state.problemIds === action.problemIds) {
        return state;
      }
      // Problem IDs changed - reload from storage
      return {
        problemIds: action.problemIds,
        completedStatus: loadCompletionFromStorage(action.dataType, action.problemIds),
      };
    }
    default:
      return state;
  }
}

/**
 * Custom hook to manage problem completion status with localStorage persistence.
 *
 * Handles:
 * - Completion status state management
 * - localStorage read/write for completion history
 * - Problem ID validation (clears history when problem set changes)
 * - Key format: `completed_${dataType}` for completion, `problem_ids_${dataType}` for validation
 */
export function useProblemCompletion(dataType: string, problems: Problem[]) {
  // Compute problem IDs to detect changes
  const currentProblemIds = useMemo(
    () => problems.map((p) => p.problem_id).join(','),
    [problems]
  );

  const [state, dispatch] = useReducer(
    reducer,
    { dataType, currentProblemIds },
    ({ dataType, currentProblemIds }) => ({
      problemIds: currentProblemIds,
      completedStatus: loadCompletionFromStorage(dataType, currentProblemIds),
    })
  );

  // Sync state when problem IDs change
  if (state.problemIds !== currentProblemIds) {
    dispatch({ type: 'SYNC_PROBLEMS', problemIds: currentProblemIds, dataType });
  }

  /**
   * Update completion status for a problem and persist to localStorage.
   */
  const updateCompletion = useCallback(
    (problemId: string, isCorrect: boolean) => {
      dispatch({ type: 'UPDATE_COMPLETION', problemId, isCorrect });

      // Also persist to localStorage
      const newStatus = {
        ...state.completedStatus,
        [problemId]: {
          is_correct: isCorrect,
          submitted_at: new Date().toISOString(),
        },
      };
      localStorage.setItem(`completed_${dataType}`, JSON.stringify(newStatus));
    },
    [state.completedStatus, dataType]
  );

  /**
   * Get status icon for a problem based on completion status.
   */
  const getStatusIcon = useCallback(
    (problemId: string) => {
      const status = state.completedStatus[problemId];
      if (!status) return dataType === 'rca' ? '🔍' : '⬜';
      return status.is_correct ? '✅' : '❌';
    },
    [state.completedStatus, dataType]
  );

  return {
    completedStatus: state.completedStatus,
    updateCompletion,
    getStatusIcon,
  };
}
