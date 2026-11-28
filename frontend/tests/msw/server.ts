import { setupServer } from "msw/node";
import { authHandlers } from "./handlers/auth";
import { draftsHandlers } from "./handlers/drafts";
import { filesHandlers } from "./handlers/files";
import { resultsHandlers } from "./handlers/results";

import { runsHandlers } from "./handlers/runs";
import { workflowsHandlers } from "./handlers/workflows";

export const server = setupServer(
  ...authHandlers,
  ...filesHandlers,
  ...draftsHandlers,
  ...runsHandlers,
  ...resultsHandlers,
  ...workflowsHandlers,
);
