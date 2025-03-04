# SPDX-License-Identifier: LGPL-2.1+

import shutil
from collections.abc import Sequence

from mkosi.architecture import Architecture
from mkosi.distributions import (
    Distribution,
    DistributionInstaller,
    PackageType,
    join_mirror,
)
from mkosi.installer.dnf import Repo, find_rpm_gpgkey, invoke_dnf, setup_dnf
from mkosi.log import die
from mkosi.state import MkosiState


class Installer(DistributionInstaller):
    @classmethod
    def pretty_name(cls) -> str:
        return "Mageia"

    @classmethod
    def filesystem(cls) -> str:
        return "ext4"

    @classmethod
    def package_type(cls) -> PackageType:
        return PackageType.rpm

    @classmethod
    def default_release(cls) -> str:
        return "cauldron"

    @classmethod
    def default_tools_tree_distribution(cls) -> Distribution:
        return Distribution.mageia

    @classmethod
    def setup(cls, state: MkosiState) -> None:
        gpgurls = (
            find_rpm_gpgkey(
                state,
                "RPM-GPG-KEY-Mageia",
                "https://mirrors.kernel.org/mageia/distrib/$releasever/$basearch/media/core/release/media_info/pubkey",
            ),
        )

        repos = []

        if state.config.local_mirror:
            repos += [Repo("core-release", f"baseurl={state.config.local_mirror}", gpgurls)]
        elif state.config.mirror:
            url = f"baseurl={join_mirror(state.config.mirror, 'distrib/$releasever/$basearch/media/core/')}"
            repos += [
                Repo("core-release", f"{url}/release", gpgurls),
                Repo("core-updates", f"{url}/updates/", gpgurls)
            ]
        else:
            url = "mirrorlist=https://www.mageia.org/mirrorlist/?release=$releasever&arch=$basearch&section=core"
            repos += [
                Repo("core-release", f"{url}&repo=release", gpgurls),
                Repo("core-updates", f"{url}&repo=updates", gpgurls)
            ]

        setup_dnf(state, repos)

    @classmethod
    def install(cls, state: MkosiState) -> None:
        cls.install_packages(state, ["filesystem"], apivfs=False)

    @classmethod
    def install_packages(cls, state: MkosiState, packages: Sequence[str], apivfs: bool = True) -> None:
        invoke_dnf(state, "install", packages, apivfs=apivfs)

        for d in state.root.glob("boot/vmlinuz-*"):
            kver = d.name.removeprefix("vmlinuz-")
            vmlinuz = state.root / "usr/lib/modules" / kver / "vmlinuz"
            if not vmlinuz.exists():
                shutil.copy2(d, vmlinuz)

    @classmethod
    def remove_packages(cls, state: MkosiState, packages: Sequence[str]) -> None:
        invoke_dnf(state, "remove", packages)

    @classmethod
    def architecture(cls, arch: Architecture) -> str:
        a = {
            Architecture.x86_64 : "x86_64",
            Architecture.arm64  : "aarch64",
        }.get(arch)

        if not a:
            die(f"Architecture {a} is not supported by Mageia")

        return a
