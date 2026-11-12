import { spawn } from "node:child_process";
import { resolve } from "node:path";

import { Plugin } from "@opencode/plugin";

type RunSlopInput = {
  path: string;
};

type RunSlopResult = {
  stdout: string;
  stderr: string;
  exitCode: number | null;
};

function runSlop(
  directory: string,
  filePath: string,
  signal: AbortSignal | undefined,
): Promise<RunSlopResult> {
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn("uv", ["run", "--no-active", "sloperator.py", filePath], {
      cwd: directory,
      signal,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout?.setEncoding("utf8");
    child.stderr?.setEncoding("utf8");

    child.stdout?.on("data", (chunk: string) => {
      stdout += chunk;
    });
    child.stderr?.on("data", (chunk: string) => {
      stderr += chunk;
    });

    child.on("error", rejectPromise);
    child.on("close", (exitCode) => {
      resolvePromise({ stdout, stderr, exitCode });
    });
  });
}

export default Plugin.define({
  id: "sloperator.run-slop",
  setup: async (ctx) => {
    await ctx.tool.transform((tools) => {
      tools.add({
        name: "run_slop",
        description:
          "Run a SlopLang program with Sloperator. Returns stdout, stderr, and exitCode as JSON.",
        input: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description:
                "Path to the .slop file, relative to the project root or absolute.",
            },
          },
          required: ["path"],
          additionalProperties: false,
        },
        options: { codemode: false },
        execute: async (input, context) => {
          const { path } = input as RunSlopInput;
          const filePath = resolve(ctx.location.directory, path);
          const result = await runSlop(
            ctx.location.directory,
            filePath,
            context.signal,
          );
          return { content: JSON.stringify(result, null, 2) };
        },
      });
    });
  },
});
