import type { StudioApi } from "../shared/types";

declare global {
  interface Window {
    bookStudio: StudioApi;
  }
}
