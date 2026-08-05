// Static file server for previewing repository HTML and SVG in the agent browser pane.
//
// Two deliberate limits, both there because an earlier version of this script
// served the whole repository on every interface:
//   1. It binds 127.0.0.1 only, so nothing on the LAN can reach it.
//   2. It serves only non-dotfile paths tracked by git. Ignored and untracked
//      files 404 even when they exist inside the repository working tree.
//
// Start it through .claude/launch.json rather than by hand: preview_start {"name": "preview"}.

const http = require("http");
const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..", "..");
const HOST = "127.0.0.1";
const PORT = 8123;

// Query git on every request instead of caching at startup. Launching one local
// process per request is slower, but publication changes take effect immediately
// and there is no stale allowlist to explain or accidentally keep serving.
function trackedFiles() {
  const output = childProcess.execFileSync("git", ["-C", ROOT, "ls-files", "-z"], {
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
    windowsHide: true,
  });
  return new Set(output.split("\0").filter(Boolean));
}

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".svg": "image/svg+xml; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/plain; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".excalidraw": "application/json; charset=utf-8",
};

function allowed(rel, tracked) {
  // rel is repo-relative with forward slashes and no leading slash.
  if (!rel || rel.split("/").some(function (seg) { return seg === "" || seg.startsWith("."); })) return false;
  return tracked.has(rel);
}

function deny(res, code, msg) {
  res.writeHead(code, { "content-type": "text/plain; charset=utf-8" });
  res.end(msg);
}

http
  .createServer(function (req, res) {
    let urlPath;
    try {
      urlPath = decodeURIComponent(req.url.split("?")[0].split("#")[0]);
    } catch (e) {
      return deny(res, 400, "bad request");
    }
    let tracked;
    try {
      tracked = trackedFiles();
    } catch (e) {
      console.error("git ls-files failed: " + e.message);
      return deny(res, 500, "unable to read tracked files");
    }
    // There is no default page. `/` lists what this server will serve, so a
    // bare localhost:8123 is useful rather than a 404.
    if (urlPath === "/") {
      res.writeHead(200, { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" });
      const count = Array.from(tracked).filter(function (rel) { return allowed(rel, tracked); }).length;
      return res.end("preview server\n\nserving non-dotfile repository files returned by git ls-files\n" +
        "currently visible: " + count + " files\n" +
        "\nrequest a repo-relative path, for example /Assets/Diagrams/galaxy-cluster.svg\n");
    }

    const rel = urlPath.replace(/^\/+/, "").replace(/\\/g, "/");
    if (!allowed(rel, tracked)) return deny(res, 404, "not found");

    const file = path.resolve(ROOT, rel);
    // Re-check after resolution so ".." cannot climb out of the repository.
    const relResolved = path.relative(ROOT, file).split(path.sep).join("/");
    if (file !== path.join(ROOT, ...rel.split("/")) || !allowed(relResolved, tracked)) {
      return deny(res, 404, "not found");
    }

    let st;
    try { st = fs.statSync(file); } catch (e) { return deny(res, 404, "not found"); }
    if (!st.isFile()) return deny(res, 404, "not found");

    res.writeHead(200, {
      "content-type": TYPES[path.extname(file).toLowerCase()] || "application/octet-stream",
      // No caching, so a reload in the pane always shows the file as it is on disk.
      "cache-control": "no-store",
    });
    fs.createReadStream(file).pipe(res);
  })
  .listen(PORT, HOST, function () {
    console.log("serving tracked repository files from " + ROOT + " on http://" + HOST + ":" + PORT);
  });
