export type ShellResponse = {
  service: string;
  version: string;
  status: "ok";
};

export const health = (): ShellResponse => ({
  service: "studio",
  version: "0.1.0",
  status: "ok",
});

