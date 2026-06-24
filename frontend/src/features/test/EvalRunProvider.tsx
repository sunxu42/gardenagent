import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  type MutableRefObject,
  type ReactNode,
} from "react";

import type { EvalWsEvent } from "@/features/test/evalWsTypes";
import {
  evalRunReducer,
  initialEvalRunRootState,
  type EvalRunAction,
  type EvalRunRootState,
} from "@/features/test/evalRunStore";

interface EvalRunContextValue {
  state: EvalRunRootState;
  dispatch: React.Dispatch<EvalRunAction>;
}

const EvalRunContext = createContext<EvalRunContextValue | null>(null);

interface EvalRunProviderProps {
  children: ReactNode;
  eventDispatchRef?: MutableRefObject<((event: EvalWsEvent) => void) | null>;
}

export function EvalRunProvider({
  children,
  eventDispatchRef,
}: EvalRunProviderProps): JSX.Element {
  const [state, dispatch] = useReducer(evalRunReducer, initialEvalRunRootState);

  useEffect(() => {
    if (!eventDispatchRef) {
      return;
    }
    eventDispatchRef.current = (event: EvalWsEvent) => {
      dispatch({ type: "WS_EVENT", payload: event });
    };
    return () => {
      eventDispatchRef.current = null;
    };
  }, [eventDispatchRef, dispatch]);

  const value = useMemo(() => ({ state, dispatch }), [state, dispatch]);

  return <EvalRunContext.Provider value={value}>{children}</EvalRunContext.Provider>;
}

export function useEvalRun(): EvalRunContextValue {
  const context = useContext(EvalRunContext);
  if (!context) {
    throw new Error("useEvalRun must be used within EvalRunProvider");
  }
  return context;
}
