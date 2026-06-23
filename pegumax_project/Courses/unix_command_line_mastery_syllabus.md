# UNIX & Command Line Mastery

*A sysadmin's path from first commands to confident automation. Live in the shell, bend it to your will, and manage real systems—local and remote—the way professionals do.*

---

## Module 1: The Shell & Filesystem Navigation
**Move through any UNIX system fluently so the command line becomes faster than any graphical interface.**

- The filesystem hierarchy, absolute vs. relative paths, and `cd`/`ls`/`pwd` fluency
- Listing power-ups: hidden files, long format, sorting, and human-readable sizes
- Tab completion, command history, and shell shortcuts that make you fast

---

## Module 2: File & Directory Operations
**Create, move, and manage files and directories with precision and without destructive mistakes.**

- `cp`, `mv`, `rm`, `mkdir`, `touch`—and safe-by-default habits to avoid disasters
- Links explained: hard links vs. symbolic links and when each matters
- Finding anything with `find` and `locate` by name, type, size, and time

---

## Module 3: Users, Permissions & Ownership
**Control who can read, write, and execute so you can secure a multi-user system correctly.**

- The permission model: read/write/execute for user, group, and other
- Setting permissions with symbolic and octal `chmod`, plus `chown` and `chgrp`
- Privilege escalation with `sudo`, the root account, and least-privilege practice

---

## Module 4: Viewing, Editing & Text Processing
**Read and transform text directly in the terminal—the heart of working on UNIX systems.**

- Viewing files with `cat`, `less`, `head`, `tail`, and live-following logs with `tail -f`
- Core text tools: `grep`, `cut`, `sort`, `uniq`, `wc`, and `tr`
- Surviving and using a terminal editor (`vim` or `nano`) for quick edits

---

## Module 5: Pipelines & Redirection
**Chain small tools into powerful one-liners by mastering how data flows between commands.**

- Standard streams: `stdin`, `stdout`, `stderr` and redirecting each (`>`, `>>`, `2>`, `&>`)
- Piping commands together with `|` to build composite operations
- Splitting and combining streams with `tee`, here-docs, and process substitution

---

## Module 6: Regular Expressions & Stream Editing
**Match, extract, and rewrite text patterns to manipulate data and logs at scale.**

- Regex fundamentals: anchors, character classes, quantifiers, and groups
- Pattern matching with `grep`/`egrep` and crafting precise search expressions
- Transforming text with `sed` and field-based processing with `awk`

---

## Module 7: Processes, Jobs & System Monitoring
**See and control everything running on a machine so you can diagnose and fix performance issues.**

- Inspecting processes with `ps`, `top`/`htop`, and understanding PIDs and resource use
- Job control: foreground/background, `&`, `jobs`, `fg`/`bg`, and `nohup`
- Signals and termination with `kill`, `pkill`, and graceful vs. forced stops

---

## Module 8: Bash Scripting
**Automate repetitive work by turning your commands into reliable, reusable scripts.**

- Script anatomy: shebang, variables, arguments, exit codes, and quoting rules
- Control flow: conditionals, `for`/`while` loops, `case`, and functions
- Robust scripting: `set -euo pipefail`, input validation, and basic error handling

---

## Module 9: Scheduling, Packages & System Services
**Manage software and automate recurring tasks the way a real administrator keeps systems running.**

- Scheduling with `cron` and `at` for recurring and one-off jobs
- Package management (`apt`/`dnf`) for installing, updating, and removing software
- Managing services and boot behavior with `systemctl` and reading logs via `journalctl`

---

## Module 10: SSH & Remote Management
**Securely access and administer remote machines—the daily reality of managing servers.**

- SSH fundamentals: connecting, host keys, and the config file for saved hosts
- Key-based authentication, `ssh-keygen`, agent forwarding, and disabling password login
- Remote workflows: `scp`/`rsync` for transfers, tunneling, and persistent sessions with `tmux`

---
