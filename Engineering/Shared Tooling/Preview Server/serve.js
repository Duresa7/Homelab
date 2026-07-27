// Static file server for previewing repository HTML and SVG in the agent browser pane.
//
// Two deliberate limits, both there because an earlier version of this script
// served the whole repository on every interface:
//   1. It binds 127.0.0.1 only, so nothing on the LAN can reach it.
//   2. It serves only the folders in ALLOW. Sensitive/ and everything else 404s.
//
// Start it through .claude/launch.json rather than by hand: preview_start {"name": "preview"}.

const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..", "..");
const HOST = "127.0.0.1";
const PORT = 8123;

// Top-level folders this server is allowed to read. Add one only when a preview
// actually needs it, and never add Sensitive/.
const ALLOW = ["Guides", "Mission Control"];

const DEFAULT = "/Mission Control/index.html";

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

function allowed(rel) {
  // rel is repo-relative with forward slashes and no leading slash.
  if (!rel || rel.split("/").some(function (seg) { return seg === "" || seg.startsWith("."); })) return false;
  const top = rel.split("/")[0];
  return ALLOW.indexOf(top) !== -1;
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
    if (urlPath === "/") urlPath = DEFAULT;

    const rel = urlPath.replace(/^\/+/, "").replace(/\\/g, "/");
    if (!allowed(rel)) return deny(res, 404, "not found");

    const file = path.resolve(ROOT, rel);
    // Re-check after resolution so ".." cannot climb out of an allowed folder.
    const relResolved = path.relative(ROOT, file).split(path.sep).join("/");
    if (file !== path.join(ROOT, ...rel.split("/")) || !allowed(relResolved)) {
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
    console.log("serving " + ALLOW.map(function (a) { return a + "/"; }).join(" and ") +
      " from " + ROOT + " on http://" + HOST + ":" + PORT);
    console.log("default page: " + DEFAULT);
  });
