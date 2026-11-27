import { setupServer } from "msw/node";
import { authHandlers } from "./handlers/auth";
import { filesHandlers } from "./handlers/files";

export const server = setupServer(...authHandlers, ...filesHandlers);
