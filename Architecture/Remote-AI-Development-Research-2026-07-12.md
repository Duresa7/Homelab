# Persistent Remote Development: My Research

**Created:** 2026-07-12  
**Last updated:** 2026-07-19

Before building a persistent remote development VM in my lab, I researched how the always-on remote coding setups I had seen actually work, what runs where, and how to reach one securely. These are my notes and the design I settled on. Every source I relied on is listed under [Sources](#sources).

## The pattern

The setup is a development machine that stays on: a cloud VPS, a homelab VM, or a small physical computer, with the repository, development tools, AI-agent CLI, credentials, and running processes all living on that machine. I connect to it from a laptop or phone through SSH, a remote editor, or a web/desktop control client. A terminal multiplexer such as `tmux`, or an agent server such as T3 Code, keeps the work alive after the client disconnects.

A homelab Ubuntu VM fills the same role as a rented VPS. The difference that matters is where the VM is hosted and how I reach it securely.

![Flow diagram: a thin client connects over a private overlay to an always-on Ubuntu VM that runs the agent runtime against the local repo and tools, with inference traffic going out to a hosted model service](Diagrams/remote-dev-pattern.svg)

## What the T3 Code project confirms

The strongest primary source is the public T3 Code repository. T3 Code is a minimal web GUI for Codex and Claude, and its remote-access documentation describes the exact arrangement I wanted [1][2]:

- A headless remote machine runs `npx t3 serve`; another device connects with a pairing link, token, or QR code.
- T3 recommends a trusted private mesh network such as a tailnet instead of exposing the server to the public internet.
- Its desktop-managed SSH flow probes the remote host, starts or reuses the remote T3 server, creates a local port forward, and saves the environment.
- In that SSH flow the remote host owns the T3 server, projects, files, Git state, terminals, and provider sessions. The local desktop is the renderer and controller.

That confirms the architecture is supported. It does not tell me which host any particular public demo runs on, so I treat demonstrations of many concurrent agent threads as evidence of the workflow layer, not proof of a specific underlying machine.

## What actually runs where

Installing Codex CLI on an Ubuntu VM makes that VM the CLI's execution environment: it reads, changes, and runs code on the machine in the selected directory. Codex also supports a remote TUI arrangement, where `codex app-server` listens on the remote machine and a TUI on another machine connects with `codex --remote`; OpenAI recommends SSH port forwarding for plain WebSockets, and authentication plus TLS for non-local connections [3][4].

There are two separate kinds of compute:

| Work | Where it runs in this design |
|---|---|
| Model inference and reasoning | OpenAI/Anthropic infrastructure, unless I deliberately run a local model |
| Git, file reads/writes, dependency installation | Remote VM |
| Type checking, compilation, tests, Docker builds | Remote VM |
| Development server and headless browser tests | Remote VM |
| Terminal or T3/VS Code user interface | Laptop or phone, with a small server component on the VM |

So a larger VM does not make the hosted model think faster. What it does is move the expensive local parts, repository indexing, package managers, builds, tests, containers, browser processes, and multiple agent harnesses, off a constrained laptop. It also removes most local application overhead when the laptop is just a terminal or browser. No GPU is needed for Codex or Claude Code against hosted models; a GPU only matters for local inference or GPU-dependent project workloads.

OpenAI's Codex cloud is a different offload model: OpenAI creates a managed container, checks out the repository, runs setup, and lets the agent work in the background [5][6]. That is useful when I do not need a self-hosted persistent machine at all.

## Persistence has three layers

1. **Machine persistence:** the VM stays powered on and its disk keeps repositories, dependencies, credentials, and artifacts.
2. **Process persistence:** `tmux`, the T3 Code server, or another supervisor keeps a running agent or dev server alive when the client disconnects. The `tmux` manual states that sessions survive SSH timeouts and intentional detach and can be reattached [7].
3. **Conversation persistence:** the agent stores session history so it can resume. Codex saves transcripts locally and supports `codex resume`; that history lives on whichever machine runs the CLI [8].

`tmux` survives a network disconnect, not a VM reboot. After a reboot a service manager can restart the long-lived servers (if their units are enabled), and agent conversations resume from their saved transcripts. That is why I do not read "persistent" as one immortal model process.

## Ways to operate it

### 1. SSH plus tmux, the simplest and most portable

Connect to the VM over a private overlay, SSH in, start one `tmux` session per project or agent, run `codex`, `claude`, dev servers, and test watchers in separate windows, then detach and reattach from any device. This is the pattern behind most "AI coding from a phone" setups. It has few moving parts and works with almost any terminal-based agent.

### 2. T3 Code remote, the closest match to the T3 project

Install and authenticate Codex or Claude on the VM, run T3 Code headlessly (or let the desktop app launch it over SSH), then connect from the T3 desktop app, a browser, phone, or tablet, keeping files, Git, terminals, and provider sessions on the VM. The SSH-launched path is attractive because it uses local port forwarding and keeps the backend on loopback instead of publishing it. Direct headless access should use the private overlay and T3's pairing controls.

### 3. Codex native remote TUI

Run the Codex app server on the VM, reach it through an SSH tunnel or authenticated `wss://`, and run the Codex TUI on the client with `codex --remote` [4]. This drops T3 Code when a terminal interface is enough.

### 4. VS Code Remote SSH

VS Code keeps the visible editor local while the VS Code server, terminal, extensions, debugger, and project run on the remote host. New integrated terminals run on the SSH host automatically, and a remote folder can be reopened inside a Dev Container on that host [9].

### 5. Provider-hosted agents

Codex cloud and Claude Code on the web already give me background, managed remote execution. They are convenient for repository-scoped tasks but are not the same as owning a durable general-purpose VM with arbitrary tools, services, network access, and files.

## Terminal control versus full computer control

For coding, "the agent controls the machine" means it reads and edits files, runs shell commands, uses Git, starts dev servers, runs tests, and calls configured tools. That is enough for most remote development and works well on a headless Ubuntu VM.

Controlling a graphical desktop, seeing pixels, clicking buttons, and typing into native applications, is a separate capability that needs a desktop session plus a computer-use tool. Anthropic documents Claude Code computer use as actual screen and application control, but its CLI implementation is macOS-only, while the Desktop version covers macOS and Windows; it also warns that computer use runs against the real desktop rather than inside the Bash sandbox [10]. A headless Ubuntu coding VM should validate web interfaces with browser automation rather than a full remote desktop. I would only add a Windows VM when a workload needs Windows builds, native Windows applications, or Windows GUI testing, and I would isolate any full GUI control from personal accounts.

## How it fits my lab

I decided the cleanest proof of concept is a dedicated Ubuntu Server VM on Galaxy, not a new public VPS:

- Start around 4 vCPU, 8 to 16 GiB RAM, and 80 to 150 GiB SSD-backed storage for web development, several agents, tests, and a few containers, then resize from observed usage.
- Apply my [Linux Host Baseline Standard](../Security/Hardening/Linux-Host-Baseline-Standard.md) before adding the workload.
- Enroll the VM directly as a NetBird peer and restrict access to a specific developer-device group. My existing [NetBird deployment](../Platforms/Netbird/README.md) already gives me a verified overlay path, so it fills the role T3's docs assign to Tailscale.
- Permit SSH only through the private overlay. No public port-forward for SSH, T3 Code, or a Codex app server.
- Use an unprivileged development account without passwordless `sudo`.
- Keep each concurrent agent in its own Git worktree and branch so agents never edit the same checkout.
- Use VM snapshots or backups for machine recovery, but treat Git commits and remote branches as the primary change history.
- Give the VM narrowly scoped repository credentials and no access to the Proxmox management plane, broad LAN shares, or unrelated secrets.

Ubuntu is my easiest first target because SSH, `tmux`, systemd, containers, and most development tooling are native. Native Windows is possible (VS Code Remote SSH supports Windows hosts and Codex runs on Windows), but WSL2 or an Ubuntu VM is simpler unless a project is Windows-specific.

## Security boundaries that matter

- **Private access first.** T3 recommends a trusted private mesh; OpenAI recommends SSH forwarding for plain WebSockets and requires authentication plus TLS for non-local connections [1][4]. I will not publish an unauthenticated agent endpoint.
- **Treat agent credentials as high value.** Codex can cache authentication on the executing host, so I protect the development user's home directory, encrypt backups, and never bake credentials into VM templates [11].
- **Sandbox and limit approvals.** Codex commands run in a constrained environment by default, with approvals governing boundary crossings, and Claude Code separates permissions from OS-level filesystem and network sandboxing [12][13].
- **Assume prompt injection is possible.** I will not give an agent administrator credentials, unrestricted secret stores, or production access just because it runs on a dedicated VM.
- **Use worktrees and review gates.** Isolate parallel agents, require tests, and review diffs before merge or deploy. Persistence raises productivity and also the time a bad autonomous action has to run.

## My decision

Start with an Ubuntu VM plus NetBird, SSH, `tmux`, and the Codex CLI. That proves remote execution, persistence, and resource offload with the fewest components. Once it is stable I will add T3 Code remote for the phone, browser, and desktop experience. Full desktop control stays out of the first phase; I add a separate Windows VM later only if a real GUI-only requirement shows up.

The first proof needs to demonstrate:

1. An agent continues a safe test task after the laptop disconnects.
2. Reconnecting restores the terminal and conversation context.
3. Builds, tests, memory use, and browser automation run on the VM.
4. The service is reachable only through NetBird or an SSH tunnel.
5. A snapshot or backup and a Git branch let me recover from a bad agent action.

## Sources

1. [T3 Code documentation](https://github.com/pingdotgg/t3code/tree/main/docs) - remote-access flow: `npx t3 serve`, pairing, private-mesh recommendation, SSH-launched port forward, and remote-owns-state model.
2. [T3 Code repository](https://github.com/pingdotgg/t3code) - the web GUI for Codex and Claude that this pattern is built around.
3. [Codex CLI](https://developers.openai.com/codex/cli) - Codex runs from a terminal and reads, changes, and runs code in the selected directory.
4. [Codex CLI features: remote app server](https://developers.openai.com/codex/cli/features#connect-the-tui-to-a-remote-app-server) - `codex app-server` and `codex --remote`, SSH forwarding for plain WebSockets, TLS for non-local.
5. [Codex cloud](https://developers.openai.com/codex/cloud) - managed background execution in an OpenAI-hosted container.
6. [Codex cloud environments](https://developers.openai.com/codex/cloud/environments) - repository checkout and setup for cloud runs.
7. [tmux(1) manual](https://man7.org/linux/man-pages/man1/tmux.1.html) - sessions survive SSH timeout and detach and can be reattached.
8. [Codex CLI features: resuming conversations](https://developers.openai.com/codex/cli/features#resuming-conversations) - local transcripts and `codex resume`.
9. [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh) - server, terminal, extensions, and debugger run on the remote host; Dev Container support.
10. [Claude Code computer use](https://code.claude.com/docs/en/computer-use) - screen and application control, macOS-only CLI, runs against the real desktop.
11. [Codex authentication](https://developers.openai.com/codex/auth) - authentication caching on the executing host.
12. [Codex sandboxing](https://developers.openai.com/codex/concepts/sandboxing) - constrained execution with approval-gated boundary crossings.
13. [Claude Code permissions](https://code.claude.com/docs/en/permissions) - permissions separate from OS-level filesystem and network sandboxing.
