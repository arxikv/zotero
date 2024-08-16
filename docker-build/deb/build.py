import argparse
import re
import shutil
import subprocess
import tempfile
from configparser import ConfigParser
from pathlib import Path
from typing import List


class DebBuilder:
    def __init__(self, staged_dir: Path, package_dir: Path, maintainer: str) -> None:
        self.staged_dir = staged_dir
        self.package_dir = package_dir
        self.maintainer = maintainer

    def get_version(self) -> str:
        # Zotero 7 moves the file to app/ directory
        for app_ini_candidate in [
            self.staged_dir / "application.ini",
            self.staged_dir / "app/application.ini",
        ]:
            if app_ini_candidate.is_file():
                app_ini = ConfigParser()
                app_ini.read(app_ini_candidate)

                return app_ini.get("App", "Version").replace("SOURCE", "ISPRAS")

        raise RuntimeError(f"Could not find application.ini in {self.staged_dir}")

    def get_apt_dependencies(self) -> List[str]:
        try:
            apt_output = subprocess.check_output(["apt-cache", "depends", "firefox"])
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("Failed to get dependencies from apt-cache") from exc

        dependencies = []
        for line in apt_output.decode().strip().split("\n"):
            match = re.match(r"^\s*Depends: (?P<pkg>.+)$", line)
            if match:
                dependencies.append(match.group("pkg"))

        dependencies.append("libegl1 | libwayland-egl1")
        dependencies.append("libegl-mesa0")

        return dependencies

    def create_desktop_entry(self, build_dir: Path):
        src_path = self.staged_dir / "zotero.desktop"

        desktop_ini = ConfigParser(interpolation=None)
        desktop_ini.optionxform = str
        desktop_ini.read(src_path)

        desktop_ini.set(
            "Desktop Entry",
            "Exec",
            "/usr/lib/zotero/zotero --url %u",
        )
        desktop_ini.set(
            "Desktop Entry",
            "Icon",
            "/usr/lib/zotero/icons/icon128.png",
        )
        desktop_ini.set(
            "Desktop Entry",
            "Categories", "Education;Office;Science;Literature;",
        )
        desktop_ini.set("Desktop Entry", "Comment", "Your personal research assistant")

        mime_types = desktop_ini.get("Desktop Entry", "MimeType")
        desktop_ini.set(
            "Desktop Entry", "MimeType", mime_types.replace("text/plain;", "")
        )

        dst_path = build_dir / "usr/share/applications/zotero.desktop"
        dst_path.parent.mkdir(parents=True)

        with dst_path.open("w") as f_dst:
            desktop_ini.write(f_dst, space_around_delimiters=False)

    def build(self):
        build_dir_tempfile = tempfile.TemporaryDirectory()
        build_dir = Path(build_dir_tempfile.name)

        control_file_path = build_dir / "DEBIAN/control"
        control_file_path.parent.mkdir()

        version = self.get_version()

        mime_dst_path = build_dir / "usr/share/mime/packages/zotero.xml"
        mime_dst_path.parent.mkdir(parents=True)
        shutil.copy("mime.xml", mime_dst_path)

        shutil.copytree(self.staged_dir, build_dir / "usr/lib/zotero")

        (build_dir / "usr/bin").mkdir()
        (build_dir / "usr/bin/zotero").symlink_to("/usr/lib/zotero/zotero")

        self.create_desktop_entry(build_dir)

        installed_size = subprocess.check_output(
            f"du -ks {build_dir / 'usr'}|cut -f 1", shell=True
        ).decode()

        with control_file_path.open("w") as f_dst:
            print("Package: zotero", file=f_dst)
            print("Architecture: amd64", file=f_dst)
            print(f"Depends: {', '.join(self.get_apt_dependencies())}", file=f_dst)
            print(f"Maintainer: {self.maintainer}", file=f_dst)
            print("Section: science", file=f_dst)
            print("Priority: optional", file=f_dst)
            print(f"Version: {version}", file=f_dst)
            print(
                "Description: Zotero is a free, easy-to-use tool to help you collect, "
                "organize, cite, and share research",
                file=f_dst,
            )
            print(f"Installed-Size: {installed_size}", file=f_dst)

        shutil.copy("postinst", build_dir / "DEBIAN/postinst")
        shutil.copy("prerm", build_dir / "DEBIAN/prerm")

        self.package_dir.mkdir(parents=True, exist_ok=True)
        package_path = self.package_dir / f"zotero_{version}_amd64.deb"
        subprocess.run(
            ["dpkg-deb", "--build", str(build_dir), str(package_path)], check=True
        )

        build_dir_tempfile.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Build Zotero .deb package")

    parser.add_argument(
        "staged_dir", type=Path, help="input directory with Zotero binaries"
    )
    parser.add_argument(
        "package_dir", type=Path, help="the parent directory of output package"
    )
    parser.add_argument(
        "maintainer", help="the maintainer's name and email (in Git commit format)"
    )

    args = parser.parse_args()
    builder = DebBuilder(**vars(args))
    builder.build()


if __name__ == "__main__":
    main()
