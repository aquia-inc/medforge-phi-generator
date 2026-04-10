# MSG Format Support — Design Document

> **Status:** Draft — not yet implemented
> **Author:** MedForge team
> **Last updated:** 2026-04-09

## Problem Statement

MedForge currently generates email documents in EML (RFC 5322) format. However, a large amount of CMS email traffic uses Office365/Outlook, where MSG is the native format. Purview classifiers may perform better when trained on MSG files that match the format they encounter in production SharePoint/Exchange environments.

## Technical Background

### What is MSG?

MSG is Microsoft's proprietary email format built on the OLE2 (Object Linking and Embedding) compound document specification. An MSG file is essentially a FAT filesystem inside a file, containing:

- **MAPI property streams** — structured binary data encoding sender, recipients, dates, importance, etc.
- **Body streams** — plain text and/or HTML body content in named sub-streams
- **Attachment sub-storages** — each attachment gets its own OLE2 storage with property and data streams

The format is documented in [MS-OXMSG](https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxmsg/) but the specification is complex (~100 pages).

### Why not just convert EML to MSG in Python?

**No pure-Python library can create MSG files.** The ecosystem:

| Library          | Language  | Can Create MSG?       | Notes                                         |
| ---------------- | --------- | --------------------- | --------------------------------------------- |
| **MsgKit**       | C# (.NET) | Yes                   | MIT license, full-featured, no Outlook needed |
| **olefile**      | Python    | No — read/modify only | Cannot create new OLE2 files from scratch     |
| **python-oxmsg** | Python    | No — read only        | Parses MSG to Python objects                  |
| **extract-msg**  | Python    | No — read only        | Extracts MSG contents                         |

Building a pure-Python MSG writer would require implementing the OLE2 container format (sector allocation, FAT chains, directory entries) plus the MAPI property encoding layer — estimated at 10-15 days with high risk of producing files that fail in Outlook edge cases.

## Recommended Approach: Docker + MsgKit CLI Tool

### Design Principles

1. **No host runtime dependencies** — no .NET, C#, or SDK installed on the developer's machine. Only Docker Desktop (already available on CMS workstations).
2. **Not a service** — the container runs once, processes files, and exits. No daemon, no ports, no orchestration.
3. **Makefile-driven** — `make msg` is the single command. Docker image is built and cached on first run.
4. **Decoupled from Python pipeline** — the generator produces EML as today. MSG conversion is a separate, optional post-processing step. The Python code never calls Docker.
5. **Alpine-based, minimal image** — multi-stage build keeps the final image small (~80MB runtime vs ~200MB SDK).

### Workflow

```
1. User generates documents as usual:
   $ uv run python -m src.cli generate --cui-positive 100 --cui-all

2. CLI output includes a hint:
   "To convert emails to Outlook MSG format: make msg RUN_DIR=output/production_run_20260409_..."

3. User runs the Makefile target:
   $ make msg RUN_DIR=output/production_run_20260409_153000

4. Makefile:
   a. Builds the Docker image (cached after first build, ~30 seconds)
   b. Runs the container with the output directory mounted as a volume
   c. Container finds all .eml files, converts to .msg, removes originals
   d. Container exits

5. Output directory now has .msg files where .eml files were
```

### Architecture

```
┌─────────────────────────────────────────────────┐
│  Host Machine (macOS/Linux/Windows)             │
│                                                 │
│  Python pipeline → output/run_*/.../*.eml       │
│                                                 │
│  $ make msg RUN_DIR=output/run_*                │
│       │                                         │
│       ▼                                         │
│  ┌──────────────────────────────────────────┐   │
│  │  Docker container (alpine, ~80MB)        │   │
│  │                                          │   │
│  │  /app/eml2msg (self-contained .NET app)  │   │
│  │       │                                  │   │
│  │       ▼                                  │   │
│  │  Reads *.eml from /data (volume mount)   │   │
│  │  Writes *.msg to /data                   │   │
│  │  Exits                                   │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
│  output/run_*/.../*.msg  ← done                 │
└─────────────────────────────────────────────────┘
```

## Implementation Details

### File Structure

```
tools/eml2msg/
  Dockerfile            # Multi-stage Alpine build
  Program.cs            # EML→MSG converter (~40 lines)
  eml2msg.csproj        # .NET 8 project file with NuGet deps
Makefile                # 'msg' target for Docker build + run
```

### Dockerfile (multi-stage Alpine)

```dockerfile
# Stage 1: Build the converter
FROM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS build
WORKDIR /src
COPY eml2msg.csproj .
RUN dotnet restore
COPY Program.cs .
RUN dotnet publish -c Release -o /app --self-contained false

# Stage 2: Minimal runtime
FROM mcr.microsoft.com/dotnet/runtime:8.0-alpine
WORKDIR /app
COPY --from=build /app .
ENTRYPOINT ["dotnet", "eml2msg.dll"]
```

Notes:
- **Alpine base** keeps the image small (~80MB final vs ~200MB Debian)
- **Multi-stage** means the SDK (~500MB) is only in the build layer, not the final image
- **Not self-contained** — uses the runtime base image's .NET, which is already there
- No hardening needed — this is a local CLI tool, not a network service

### C# Converter (Program.cs)

```csharp
using MsgKit;
using MimeKit;

if (args.Length < 1)
{
    Console.Error.WriteLine("Usage: eml2msg <directory> [--ratio 0.5] [--keep-eml]");
    return 1;
}

var directory = args[0];
var ratio = 0.5;
var keepEml = false;

for (int i = 1; i < args.Length; i++)
{
    if (args[i] == "--ratio" && i + 1 < args.Length)
        ratio = double.Parse(args[++i]);
    if (args[i] == "--keep-eml")
        keepEml = true;
}

var rng = new Random();
var emlFiles = Directory.GetFiles(directory, "*.eml", SearchOption.AllDirectories);
var converted = 0;
var skipped = 0;

foreach (var emlPath in emlFiles)
{
    if (rng.NextDouble() > ratio)
    {
        skipped++;
        continue;
    }

    try
    {
        var mimeMessage = MimeMessage.Load(emlPath);
        var msgPath = Path.ChangeExtension(emlPath, ".msg");

        var senderAddr = mimeMessage.From.Mailboxes.FirstOrDefault();
        using var email = new Email(
            new Sender(
                senderAddr?.Address ?? "unknown@example.com",
                senderAddr?.Name ?? ""),
            mimeMessage.Subject ?? "");

        foreach (var to in mimeMessage.To.Mailboxes)
            email.Recipients.AddTo(to.Address, to.Name ?? "");
        foreach (var cc in mimeMessage.Cc.Mailboxes)
            email.Recipients.AddCc(cc.Address, cc.Name ?? "");

        email.BodyText = mimeMessage.TextBody ?? "";
        email.BodyHtml = mimeMessage.HtmlBody ?? "";

        if (mimeMessage.Date != default)
            email.SentOn = mimeMessage.Date.UtcDateTime;

        foreach (var attachment in mimeMessage.Attachments)
        {
            if (attachment is MimePart part)
            {
                using var stream = new MemoryStream();
                part.Content.DecodeTo(stream);
                stream.Position = 0;
                email.Attachments.Add(stream, part.FileName ?? "attachment", -1, false);
            }
        }

        email.Save(msgPath);

        if (!keepEml)
            File.Delete(emlPath);

        converted++;
    }
    catch (Exception ex)
    {
        Console.Error.WriteLine($"Failed: {Path.GetFileName(emlPath)}: {ex.Message}");
    }
}

Console.WriteLine($"Converted: {converted}, Skipped: {skipped}, Total: {emlFiles.Length}");
return 0;
```

### .NET Project File (eml2msg.csproj)

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="MsgKit" Version="3.*" />
    <PackageReference Include="MimeKit" Version="4.*" />
  </ItemGroup>
</Project>
```

### Makefile Targets

```makefile
# Docker image name for the EML→MSG converter
EML2MSG_IMAGE := medforge-eml2msg
RUN_DIR ?= $(shell ls -td output/production_run_* 2>/dev/null | head -1)
MSG_RATIO ?= 0.5

.PHONY: msg msg-build msg-help

msg-build:
	@docker build -t $(EML2MSG_IMAGE) tools/eml2msg/

msg: msg-build
	@if [ -z "$(RUN_DIR)" ]; then \
		echo "Error: No run directory found. Specify with RUN_DIR=output/production_run_..."; \
		exit 1; \
	fi
	@echo "Converting EML→MSG in $(RUN_DIR) (ratio=$(MSG_RATIO))..."
	timeout 600 docker run --rm --network none \
		-v "$(PWD)/$(RUN_DIR):/data" \
		$(EML2MSG_IMAGE) \
		/data --ratio $(MSG_RATIO)
	@echo "Done. MSG files written to $(RUN_DIR)"

msg-help:
	@echo "MSG Conversion (requires Docker Desktop)"
	@echo ""
	@echo "  make msg                    Convert latest run (50% EML→MSG)"
	@echo "  make msg RUN_DIR=output/... Convert specific run directory"
	@echo "  make msg MSG_RATIO=1.0      Convert all EMLs to MSG"
	@echo "  make msg MSG_RATIO=0        Skip conversion (keep all EML)"
```

### Python CLI Integration (hint only)

No Docker calls from Python. The generator just prints a hint after completion:

```python
# At the end of generate() in cli.py, after stats are printed:
if any(fmt == 'eml' for fmt in stats['by_format']):
    console.print(
        f"\n[dim]To convert emails to Outlook MSG format:[/dim]\n"
        f"  [cyan]make msg RUN_DIR={run_dir.relative_to('.')}[/cyan]\n"
        f"  [dim](requires Docker Desktop)[/dim]"
    )
```

## Testing Plan

### Converter Functional Tests

Run from inside the Docker container or via `make msg-test`:

| Test                | Input                                            | Expected                                          | Validates            |
| ------------------- | ------------------------------------------------ | ------------------------------------------------- | -------------------- |
| Basic EML → MSG     | Simple text-only EML                             | .msg file with matching subject, sender, body     | Core conversion path |
| HTML body           | EML with text + HTML parts                       | .msg with `BodyText` and `BodyHtml` populated     | Multipart handling   |
| With attachment     | EML with PDF attachment                          | .msg with attachment, matching filename and bytes | Attachment fidelity  |
| Multiple recipients | EML with To + Cc                                 | .msg with all recipients in correct fields        | Recipient parsing    |
| Unicode content     | EML with UTF-8 subject/body (e.g., em-dash, CJK) | .msg with content preserved                       | Encoding survival    |
| Malformed EML       | Truncated or garbled file                        | Error logged, file skipped, conversion continues  | Graceful failure     |
| Empty directory     | No .eml files                                    | Exit 0, "Converted: 0" message                    | No-op safety         |
| Ratio=0             | `--ratio 0` flag                                 | All EML files remain, zero .msg created           | Skip logic           |
| Ratio=1.0           | `--ratio 1.0` flag                               | All EML files converted                           | Full conversion      |

### Integration Tests (Makefile / Docker)

| Test               | Command                            | Expected                                          |
| ------------------ | ---------------------------------- | ------------------------------------------------- |
| Docker not running | `make msg` with Docker stopped     | Clear error: "Cannot connect to Docker daemon"    |
| Missing RUN_DIR    | `make msg RUN_DIR=nonexistent/`    | Error: "No run directory found"                   |
| Re-run idempotency | `make msg` twice on same directory | Second run converts 0 files (no .eml left)        |
| Timeout safety     | Large batch (1000+ emails)         | Completes within `timeout` limit or exits cleanly |

### Outlook Validation Checklist (Manual)

After conversion, open 5-10 .msg files in Outlook and verify:

- [ ] Sender name and address display correctly
- [ ] To/Cc recipients are populated
- [ ] Subject line matches original EML
- [ ] Plain text body is readable
- [ ] HTML body renders (if present)
- [ ] Attachments are present, correct size, and openable
- [ ] Date/time matches original
- [ ] No security warnings or macro prompts on open

## Security Considerations

### Volume Mount Scope

The Makefile mounts **only the specific run directory** — not the project root or home directory:

```makefile
docker run --rm -v "$(PWD)/$(RUN_DIR):/data" ...
```

The container can read/write only under `/data`. It has no access to source code, credentials, or `.env` files.

### Network Isolation

The converter needs no internet access. Add `--network none` to the `docker run` command:

```makefile
docker run --rm --network none -v "$(PWD)/$(RUN_DIR):/data" $(EML2MSG_IMAGE) /data
```

This prevents any outbound connections from the container — defense in depth even though the tool makes no network calls.

### No Secrets or Credentials

The container receives zero environment variables, no API keys, no credentials. It reads `.eml` files from a mounted directory and writes `.msg` files to the same directory. Nothing else.

### OLE2 / Macro Injection

MSG files are OLE2 containers that can theoretically contain VBA macros. However:
- **MsgKit does not support embedding macros** — it creates standard email messages only
- We control all input EML content (generated by our own faker/LLM pipeline)
- No external or untrusted content enters the conversion pipeline

### File Ownership

The container runs as root by default. Files written to the mount will be owned by `root:root` on Linux. On macOS (Docker Desktop), files inherit the host user's permissions. If Linux ownership is a concern, add `--user $(id -u):$(id -g)` to the docker run command:

```makefile
docker run --rm --user $$(id -u):$$(id -g) -v "$(PWD)/$(RUN_DIR):/data" ...
```

## Operational Resilience

### Hangs and Timeouts

| Risk                                                                    | Mitigation                                                        |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Container hangs on malformed EML                                        | Per-file try/catch in C# — logs error, skips to next file         |
| Docker `--rm` hang (known Docker CLI bug when container fails to start) | Wrap with `timeout` shell command as safety net                   |
| Unexpectedly large batch (10,000+ EMLs)                                 | Sequential processing, no memory accumulation — handles any count |

Updated Makefile with timeout:

```makefile
msg: msg-build
	@if [ -z "$(RUN_DIR)" ]; then \
		echo "Error: No run directory found."; exit 1; fi
	@echo "Converting EML→MSG in $(RUN_DIR) (ratio=$(MSG_RATIO))..."
	timeout 600 docker run --rm --network none \
		-v "$(PWD)/$(RUN_DIR):/data" \
		$(EML2MSG_IMAGE) \
		/data --ratio $(MSG_RATIO)
	@echo "Done. MSG files written to $(RUN_DIR)"
```

The 10-minute timeout (`timeout 600`) is generous — typical conversion is <1 second per file.

### Idempotency and Resumability

| Scenario                            | Behavior                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| Conversion interrupted mid-batch    | Some files are .msg, some remain .eml                                          |
| Re-run `make msg` on same directory | Only processes remaining .eml files — already-converted .msg files are ignored |
| Want to re-convert from scratch     | Re-generate the EML files first (they're the source of truth)                  |
| Want to keep EML alongside MSG      | Pass `--keep-eml` flag to the converter                                        |

The tool is **naturally idempotent** because it only looks for `.eml` files. Once an EML is converted and deleted, it won't be processed again.

### Progress Reporting

The C# tool prints a summary on exit:
```
Converted: 47, Skipped: 53, Total: 100
```

For large batches, consider adding per-file progress output:
```
[  1/100] Converting Snyk_0001.eml → Snyk_0001.msg
[  2/100] Converting KMP_0002.eml → KMP_0002.msg
...
```

## Known Gaps and Considerations

### Manifest becomes stale after conversion

`cui_manifest.json` references files as `SomeDoc_0001.eml`. After `make msg` converts the file, the path on disk is `SomeDoc_0001.msg` but the manifest still says `.eml`.

**Recommended approach:** Add a `make msg-fixup-manifest` target that runs a small Python script to update `.eml` → `.msg` in the manifest for any converted files. This keeps the fix in Python (where the manifest is already managed) and avoids adding JSON logic to the C# tool.

```python
# tools/fixup_manifest.py (sketch)
import json, os, sys

manifest_path = os.path.join(sys.argv[1], 'metadata', 'cui_manifest.json')
with open(manifest_path) as f:
    manifest = json.load(f)

for entry in manifest.get('files', []):
    eml_path = os.path.join(sys.argv[1], entry['file_path'])
    msg_path = eml_path.rsplit('.', 1)[0] + '.msg'
    if not os.path.exists(eml_path) and os.path.exists(msg_path):
        entry['file_path'] = entry['file_path'].rsplit('.', 1)[0] + '.msg'
        entry['format'] = 'msg'

with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
```

The `make msg` target should call this automatically after conversion completes.

### Fidelity validator does not handle MSG

`validate_file_fidelity.py` validates EML/DOCX/PDF/XLSX/PPTX but has no MSG validation path. After conversion, MSG files would be skipped or cause validation errors.

**Recommended workflow:** Run validation **before** conversion:

```bash
# 1. Generate
uv run python -m src.cli generate --cui-positive 100 --cui-all

# 2. Validate (while files are still EML)
uv run python tests/validate_file_fidelity.py output/production_run_*/

# 3. Convert (validated EMLs → MSG)
make msg RUN_DIR=output/production_run_*
```

If MSG-specific validation is needed later, add a check that opens each MSG with `extract-msg` (Python, read-only) to verify subject/sender/attachment count match the manifest.

### Custom MIME headers may not survive conversion

Our BugCrowd and ServiceNow generators set custom headers:
- `Thread-Topic` → maps to MAPI `PR_CONVERSATION_TOPIC` (should survive)
- `X-MS-Exchange-Organization-RecordReviewCfmType` → non-standard, may be silently dropped
- `X-Mailgun-Tag` (Snyk emails) → will be dropped (not a MAPI property)

**Impact:** Low. These headers add realism but are not what Purview classifies on. The core content (subject, body, attachments, sender/recipient) all survive conversion. Custom X-headers are cosmetic.

**Mitigation:** Add a conversion test that compares a known EML's headers against the resulting MSG's MAPI properties to document exactly which headers survive.

### `--keep-eml` creates training duplicates

If a user passes `--keep-eml` and uploads the entire output directory to Purview, the classifier sees the same content twice in different formats. This can bias training.

**Guidance:** `--keep-eml` is for **validation and debugging only**. Before uploading to Purview for training, ensure the output directory contains only one format per document — either EML or MSG, not both. The default behavior (delete EML after successful conversion) is correct for production use.

### Windows Makefile compatibility

The `timeout` command used in the Makefile is a GNU coreutils utility available on Linux and macOS. It is not available natively on Windows cmd or PowerShell.

**Workarounds for Windows users:**
- **WSL2 (recommended):** Run `make msg` from a WSL2 terminal. Docker Desktop integrates with WSL2.
- **Git Bash:** Ships with `timeout` via MSYS2.
- **PowerShell alternative:** Replace with `Start-Process -Wait -Timeout` in a separate `msg.ps1` script.

Add to prerequisites: "On Windows, run from WSL2 or Git Bash terminal."

## Level of Effort

| Phase                      | LOE          | Description                                                  |
| -------------------------- | ------------ | ------------------------------------------------------------ |
| Design doc (this document) | 0.5 day      | Done                                                         |
| C# tool + Dockerfile       | 1 day        | Program.cs, csproj, Dockerfile, local build test             |
| Makefile targets           | 0.5 day      | `msg`, `msg-build`, `msg-help` targets                       |
| Manifest fixup script      | 0.5 day      | `fixup_manifest.py` + wire into `make msg`                   |
| Python CLI hint            | 0.5 day      | Print `make msg` suggestion after EML generation             |
| Testing                    | 1 day        | Functional tests, header survival audit, Outlook validation  |
| **Total**                  | **4 days**   |                                                              |

## Prerequisites

- Docker Desktop installed and running
- On Windows: run from WSL2 or Git Bash terminal (for `make` and `timeout` compatibility)
- No other runtime dependencies on host

## Acceptance Criteria

**Functional:**
- [ ] `make msg` converts EML files to MSG format using Docker
- [ ] Docker image is Alpine-based and cached after first build
- [ ] `MSG_RATIO` controls what fraction of EMLs become MSG (default 50%)
- [ ] MSG files open correctly in Outlook (sender, recipients, subject, body, attachments)
- [ ] Works on macOS, Linux, and Windows (Docker Desktop)
- [ ] No .NET, C#, or SDK installed on host machine
- [ ] Python generator prints `make msg` hint after generating EML files

**Resilience:**
- [ ] Malformed EML files are skipped with error log, conversion continues
- [ ] Re-running `make msg` on the same directory is safe (idempotent)
- [ ] 10-minute timeout prevents infinite hangs
- [ ] Graceful error message if Docker is not running

**Data integrity:**
- [ ] Manifest is updated after conversion (`.eml` paths → `.msg`)
- [ ] Run fidelity validation before conversion (while files are still EML)
- [ ] `--keep-eml` is documented as debug-only, not for Purview upload
- [ ] Custom MIME header survival is audited and documented

**Security:**
- [ ] Container mounts only the specific run directory (not project root)
- [ ] `--network none` prevents any outbound connections
- [ ] No secrets, API keys, or credentials passed to container
- [ ] No macro/VBA content in generated MSG files

## Decision Record

| Field                     | Value                                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Decision**              | Document options for future implementation                                                            |
| **Recommended approach**  | Docker-based EML→MSG post-processing with MsgKit                                                      |
| **Status**                | Deferred                                                                                              |
| **Reason for deferral**   | Current EML format works for Purview training; MSG adds value but is not blocking                     |
| **Trigger to implement**  | CMS reports that EML format is insufficient for Purview classifier accuracy on Outlook-native content |
| **Alternatives rejected** | Pure Python (too complex), local .NET SDK (host dependency), Graph API (requires internet + Azure)    |
