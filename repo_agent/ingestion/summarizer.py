
import json
from datetime import datetime
from .scanner import ScanResult
from .tech_detector import TechProfile


class RepoSummarizer:

    def __init__(self, scan: ScanResult, profile: TechProfile):
        self.scan = scan
        self.profile = profile

    def build_manifest(self) -> dict:
        top_extensions = sorted(
            self.scan.extension_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        total_kb = self.scan.total_size_bytes / 1024

        manifest = {
            "schema_version": "1.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "repository": {
                "name": self.scan.repo_name,
                "root": self.scan.repo_root,
                "total_files": self.scan.total_files,
                "total_size_kb": round(total_kb, 2),
                "top_extensions": dict(top_extensions),
            },
            "tech_profile": {
                "primary_language": self.profile.primary_language,
                "languages": self.profile.languages,
                "frameworks": self.profile.frameworks,
                "build_tools": self.profile.build_tools,
                "has_tests": self.profile.has_tests,
                "has_ci": self.profile.has_ci,
                "config_files": self.profile.config_files_found,
            },
            "entry_points": self.profile.entry_points,
            "python_files": [
                f.path for f in self.scan.files
                if f.extension == ".py" and not f.is_binary
            ],
        }

        return manifest

    def build_human_summary(self, manifest: dict) -> str:
        r = manifest["repository"]
        t = manifest["tech_profile"]

        lines = [
            f"# Repository: {r['name']}",
            "",
            f"**Size:** {r['total_files']} files, {r['total_size_kb']} KB",
            f"**Primary language:** {t['primary_language']}",
        ]

        if t["languages"]:
            lines.append(f"**All languages:** {', '.join(t['languages'])}")
        if t["frameworks"]:
            lines.append(f"**Frameworks detected:** {', '.join(t['frameworks'])}")
        if t["build_tools"]:
            lines.append(f"**Build tools:** {', '.join(t['build_tools'])}")

        lines.append(f"**Has tests:** {'Yes' if t['has_tests'] else 'No'}")
        lines.append(f"**Has CI:** {'Yes' if t['has_ci'] else 'No'}")

        if manifest["entry_points"]:
            lines.append(f"\n**Entry points:**")
            for ep in manifest["entry_points"]:
                lines.append(f"  - {ep}")

        top_ext = list(r["top_extensions"].items())[:5]
        if top_ext:
            lines.append(f"\n**File breakdown:**")
            for ext, count in top_ext:
                lines.append(f"  - {ext or '(no ext)'}: {count} files")

        return "\n".join(lines)

    def save_manifest(self, output_path: str = "data/manifest.json") -> str:
        manifest = self.build_manifest()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"✓ Manifest saved to {output_path}")
        return output_path
