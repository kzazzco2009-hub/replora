import { setupServer } from "msw/node";
import { authHandlers } from "./handlers/auth";
import { draftsHandlers } from "./handlers/drafts";
import { filesHandlers } from "./handlers/files";

import { runsHandlers } from "./handlers/runs";

export const server = setupServer(
  ...authHandlers,
  ...filesHandlers,
  ...draftsHandlers,
  ...runsHandlers,
);
