/* eslint-disable @typescript-eslint/no-explicit-any */
import axios from "@/lib/axios";

import { createRoot } from "react-dom/client";
import { createInertiaApp } from "@inertiajs/react";
import { Toaster } from "@/components/ui/sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "../main.css";
import { WebSocketProvider } from "./contexts/websocket-provider";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

const pages = import.meta.glob("./pages/**/*.tsx");

document.addEventListener("DOMContentLoaded", () => {
  axios.defaults.xsrfCookieName = "csrftoken";
  axios.defaults.xsrfHeaderName = "X-CSRFToken";

  createInertiaApp({
    resolve: async (name) => {
      const importer = pages[`./pages/${name}.tsx`] as
        | (() => Promise<{ default: any }>)
        | undefined;
      if (!importer) {
        throw new Error(`Page not found: ${name}`);
      }
      const page = (await importer()).default;
      return page;
    },
    setup({ el, App, props }) {
      createRoot(el).render(
        <QueryClientProvider client={queryClient}>
          <WebSocketProvider>
            <App {...props} />
            <Toaster position="top-center" />
          </WebSocketProvider>
        </QueryClientProvider>,
      );
    },
  });
});
