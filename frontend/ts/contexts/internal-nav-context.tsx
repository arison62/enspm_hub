/* eslint-disable @typescript-eslint/no-explicit-any */
// frontend/ts/contexts/InternalNavContext.tsx
import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
} from "react";
import { EventEmitter } from "events";

/**
 * Interface pour un élément de la pile de navigation
 */
export interface NavItem {
  id: string;
  component: React.ComponentType<any>;
  props: any;
  title: string;
}

/**
 * Types d'événements supportés par le navigateur interne
 */
export const NAV_EVENT_TYPE = {
  ON_PUSH:  "ON_PUSH",
  ON_POP : "ON_POP",
  ON_RESET: "ON_RESET",
} as const

interface InternalNavContextType {
  stack: NavItem[];
  currentView: NavItem;
  push: (
    component: React.ComponentType<any>,
    title: string,
    props?: any,
  ) => void;
  pop: () => void;
  goToIndex: (index: number) => void;
  navEmitter: EventEmitter;
}

const InternalNavContext = createContext<InternalNavContextType | undefined>(
  undefined,
);

export const InternalNavProvider: React.FC<{
  children: React.ReactNode;
  initialPage: React.ComponentType<any>;
  initialTitle: string;
}> = ({ children, initialPage, initialTitle }) => {
  const [stack, setStack] = useState<NavItem[]>([
    { id: "root", component: initialPage, title: initialTitle, props: {} },
  ]);

  // Initialisation de l'émetteur d'événements
  const navEmitter = useMemo(() => new EventEmitter(), []);

  // Vue actuelle (dernier élément de la pile)
  const currentView = useMemo(() => stack[stack.length - 1], [stack]);

  const push = useCallback(
    (component: React.ComponentType<any>, title: string, props: any = {}) => {
      const id = Math.random().toString(36).substring(7);

      // Logger l'événement pour le monitoring frontend
      console.info(`[Nav] Pushing view: ${title}`);
      navEmitter.emit(NAV_EVENT_TYPE.ON_PUSH, { title, id });

      setStack((prev) => [...prev, { id, component, title, props }]);
    },
    [navEmitter],
  );

  const pop = useCallback(() => {
    if (stack.length <= 1) return;

    navEmitter.emit(NAV_EVENT_TYPE.ON_POP, { poppedView: currentView.title });
    setStack((prev) => prev.slice(0, -1));
  }, [stack.length, currentView, navEmitter]);

  const goToIndex = useCallback(
    (index: number) => {
      setStack((prev) => {
        const newStack = prev.slice(0, index + 1);
        navEmitter.emit(NAV_EVENT_TYPE.ON_RESET, { depth: newStack.length });
        return newStack;
      });
    },
    [navEmitter],
  );

  // Nettoyage des listeners au démontage
  useEffect(() => {
    return () => {
      navEmitter.removeAllListeners();
      console.log("InternalNavProvider unmounted");
    };
  }, [navEmitter]);

  const value = useMemo(
    () => ({
      stack,
      currentView,
      push,
      pop,
      goToIndex,
      navEmitter,
    }),
    [stack, currentView, push, pop, goToIndex, navEmitter],
  );

  return (
    <InternalNavContext.Provider value={value}>
      {children}
    </InternalNavContext.Provider>
  );
};

export const useInternalNav = () => {
  const context = useContext(InternalNavContext);
  if (!context) {
    throw new Error("useInternalNav must be used within InternalNavProvider");
  }
  return context;
};
