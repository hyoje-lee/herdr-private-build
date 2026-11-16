"""Pinned, fail-closed source transformations. Never edit the upstream checkout."""
from pathlib import Path
import difflib

PINS = {
    "herdr-core": "bb8a2f7740fd308e520e4e9361c292c993c7f08e",
    "herdr-app": "8e1208deeff2a24441a192974e648c6fa0c5053c",
    "herdr-core/vendor/ghostty": "1e5cdb865807abc990181efb8ebfa9122955cce2",
    "herdr-app/vendor/ghostty": "291fd050b9e9c293c8adb6a140742649b7e42d3a",
}
POLICY = "herdr-private-v1"
DENIED = 'Err("Disabled in this private build; use the component build/install script".into())'


def apply(root: Path, component=None) -> str:
    originals = {}

    def replace(file, old, new):
        if component and not file.startswith(f"herdr-{component}/"):
            return
        path = root / file
        text = path.read_text()
        if text.count(old) != 1:
            raise RuntimeError(f"Patch context mismatch: {file}: {old[:90]!r}")
        originals.setdefault(file, text)
        path.write_text(text.replace(old, new, 1))

    def gate(file, signature, result):
        # An unconditional return cannot be undone by settings or environment.
        replace(file, signature, '#[allow(unreachable_code, unused_variables)]\n' +
                signature + '\n    // HERDR-PRIVATE: enforced in the binary.\n    return ' + result + ';')

    app = "herdr-app/src/"
    core = "herdr-core/crates/herdr-core/src/"
    gate(app + "telemetry.rs", "fn read_env_off() -> Option<&'static str> {", 'Some("private-build")')
    gate(app + "telemetry.rs", "fn endpoint() -> Option<String> {", "None")
    gate(app + "telemetry.rs", "fn post(url: &str, body: &str) -> Option<u16> {", "None")
    gate(app + "telemetry.rs", "pub fn start(setting: bool) {", "()")
    gate(app + "telemetry.rs", "pub fn set_setting(on: bool) {", "()")
    gate(app + "telemetry.rs", "pub fn status() -> Value {",
         'serde_json::json!({"enabled": false, "setting": false, "sends": false, "off_because": "private-build", "endpoint": null, "draft": null, "queued": [], "last_sent": null})')
    gate(app + "feedback.rs", "fn endpoint() -> Option<String> {", "None")
    gate(app + "feedback.rs", "fn post(url: &str, body: &str, files: &[PathBuf]) -> Result<(), String> {", DENIED)
    for signature, result in [
        ("fn checks_app() -> Option<PathBuf> {", "None"),
        ("fn checks_core() -> bool {", "false"),
        ("pub fn start() {", "()"),
        ("pub fn update_core() {", "()"),
        ("fn curl_text(url: &str) -> Result<String, String> {", DENIED),
        ("fn unpack(url: &str, sha: &str, work: &Path) -> Result<PathBuf, String> {", DENIED),
        ("pub fn apply_on_startup() -> bool {", "false"),
        ("pub fn apply() -> std::io::Result<bool> {", "Ok(false)"),
        ("pub fn after_update(connected: std::sync::Arc<crate::hc::Core>) {", "()"),
    ]:
        gate(app + "update.rs", signature, result)
    gate(app + "update_notes.rs", "fn fetch_media(notes: &[Note]) {", "()")
    gate(app + "core_bin.rs", "pub fn install() -> Result<PathBuf, String> {", DENIED)
    gate(app + "core_bin.rs", "pub fn update_to(at_least: Option<&str>) -> Result<String, String> {", DENIED)
    gate(app + "core_bin.rs", "fn ensure_core_bundle(version: &str) -> Result<(), String> {", DENIED)
    # Use the core shipped alongside this app, not an old PATH/settings binary.
    gate(app + "core_bin.rs", "pub fn find(configured: Option<&str>) -> Option<PathBuf> {",
         'std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.join("herdr-core"))).filter(|p| p.is_file())')
    gate(core + "releases.rs", "fn curl(url: &str, to: &Path) -> Result<(), RpcError> {",
         'Err(RpcError::new("refused", "Downloads disabled in private build", "Build the private core for the destination platform"))')
    # --from must not replace the hardened binary with an ordinary release either.
    gate(core + "cli/update.rs", "pub(super) fn update(paths: &Paths, from: &std::path::Path, force: bool) -> Result<Out, RpcError> {",
         'Err(RpcError::new("refused", "Self-update disabled in private build", "Use the private build installer"))')
    # No HTTP/TCP/WebSocket from JavaScript. Explicit process/SSH operations remain.
    replace(app + "mods.rs", ".network(NetworkGrant::Unrestricted)", ".network(NetworkGrant::Denied)")
    dep = "herdr-app/vendor/gpui-kit/crates/shell/src/dependencies.rs"
    signature = "    ) -> Result<BTreeMap<String, MaterializedDependency>> {"
    replace(dep, signature, signature + '\n        if !manifest.dependencies().is_empty() {\n            bail!("Runtime Git dependencies are disabled in private builds; vendor reviewed modules locally");\n        }')
    # Identify the binary without contacting a running core or modifying state.
    for file, text in [(app + "main.rs", 'fn main() {'), (core + "main.rs", 'fn main() {')]:
        replace(file, text, text + '\n    if std::env::args().nth(1).as_deref() == Some("--private-build") {\n' +
                f'        println!("{POLICY}");\n        return;\n    }}')

    # Regressions execute only these gates; fake endpoints/curl must never be reached.
    additions = {
        app + "telemetry.rs": '''
#[cfg(test)]
mod private_policy_tests {
    #[test] fn private_policy_telemetry() {
        assert_eq!(super::read_env_off(), Some("private-build"));
        assert!(super::endpoint().is_none());
        super::start(true);
        assert!(super::TX.get().is_none());
        super::set_setting(true);
        assert!(!super::collecting());
        assert!(super::post("http://127.0.0.1:9", "secret").is_none());
    }
}
''',
        app + "feedback.rs": '''
#[cfg(test)]
mod private_policy_tests {
    #[test] fn private_policy_feedback() {
        assert!(!super::available());
        assert!(super::post("http://127.0.0.1:9", "secret", &[]).is_err());
    }
}
''',
        app + "update.rs": '''
#[cfg(test)]
mod private_policy_tests {
    #[test] fn private_policy_updates() {
        assert!(super::checks_app().is_none());
        assert!(!super::checks_core());
        super::start();
        assert!(!super::RUNNING.load(std::sync::atomic::Ordering::Relaxed));
        super::update_core();
        assert!(!super::apply_on_startup());
        assert!(!super::apply().unwrap());
        assert!(super::curl_text("http://127.0.0.1:9").is_err());
        assert!(super::unpack("http://127.0.0.1:9", "", std::path::Path::new("/nonexistent")).is_err());
    }
}
''',
        core + "releases.rs": '''
#[cfg(test)]
mod private_policy_tests {
    #[test] fn private_policy_download() {
        assert!(super::curl("http://127.0.0.1:9", std::path::Path::new("/nonexistent")).is_err());
    }
}
''',
    }
    for file, addition in additions.items():
        if component and not file.startswith(f"herdr-{component}/"):
            continue
        path = root / file
        path.write_text(path.read_text() + addition)
    diff = []
    for file, before in originals.items():
        diff.extend(difflib.unified_diff(before.splitlines(True), (root / file).read_text().splitlines(True),
                                         fromfile="a/" + file, tofile="b/" + file))
    return "".join(diff)
