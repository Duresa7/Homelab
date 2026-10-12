# Andor-ParrotOS-PC NVIDIA Driver Installation

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

**Implementation date:** 2026-10-11  
**Status:** Complete  
**Affected systems:** [Andor-ParrotOS-PC](../../Workstations/Andor-ParrotOS-PC.md)

On 2026-10-11 I installed NVIDIA driver 615.71.09 on Andor-ParrotOS-PC for its RTX 3070, using the open kernel modules. After a reboot the card runs on it, and so does the KDE Plasma Wayland desktop.

## Starting state

- The card (`10de:2488`, an MSI board) ran on `nouveau`. No NVIDIA driver package was installed, only `firmware-nvidia-graphics`.
- Parrot's repositories offered `nvidia-driver` 550.163.01.
- NVIDIA's `latest.txt` named 595.71.05. That pointer is stale: 595.91.07, 610.57.04 and 615.71.09 are all published on NVIDIA's download server.
- NVIDIA's official Debian 13 repository offered `nvidia-open` up to 615.71.09-2. I took 615.71.09, the newest.
- Secure Boot is off (`SecureBoot=0`, `SetupMode=0`), so the DKMS module needs no signing key.
- Two kernels were installed: 7.0.9, which was running, and 7.1.13, the GRUB default that had not been booted yet. Headers were present for both.

## What changed

1. **Repository.** I installed NVIDIA's `cuda-keyring` 1.1-1 (`d0d4ef98…`). It adds `/etc/apt/sources.list.d/cuda-debian13-x86_64.list`, signed by `/usr/share/keyrings/cuda-archive-keyring.gpg`.
2. **Pin.** The first simulation failed. Parrot's `/etc/apt/preferences.d/parrot-pinning` gives its own suites priority 600, above the default 500 that NVIDIA's repository gets. apt therefore chose Parrot's 550 `nvidia-settings`, `nvidia-xconfig` and `nvidia-opencl-icd` against 615 dependencies. I added `/etc/apt/preferences.d/nvidia-cuda-repo`, which gives NVIDIA's origin priority 650 for the driver package names only (`nvidia-*`, `libnvidia-*`, `libcuda*`, `libnvcuvid*`, `libnvoptix*`, `libxnvctrl*`, `firmware-nvidia-gsp*`, the NVIDIA GL/EGL/GLES libraries and `xserver-xorg-video-nvidia*`). Every other package still comes from Parrot.
3. **Install.** The second simulation planned 52 installs and no removals: 47 packages at 615.71.09, NVIDIA's four EGL platform libraries, and `libgles1` from Parrot. `apt-get install nvidia-open` exited 0 at 10:14 PM Eastern. DKMS reports `nvidia/615.71.09` installed for both kernels, and `modinfo` reads 615.71.09 for each. The package set `blacklist nouveau` in `/etc/modprobe.d/nvidia.conf`. The 7.1.13 initramfs was rebuilt with it, and I rebuilt the 7.0.9 initramfs so the fallback kernel matches.
4. **Reboot** at 10:49 PM Eastern. The machine came back on kernel 7.1.13.

## Verification

- `lspci -k`: kernel driver in use `nvidia`. Loaded modules are `nvidia`, `nvidia_modeset`, `nvidia_drm` and `nvidia_uvm`, with no `nouveau`. `nvidia_drm.modeset=Y`.
- `nvidia-smi`: NVIDIA GeForce RTX 3070, driver 615.71.09, VBIOS 94.04.46.00.F2, 8192 MiB, P8 at idle, 40 °C, 17 W of 220 W, PCIe 4.0 x16.
- The graphical session is Wayland. `kwin_wayland`, `Xwayland` and `plasmashell` are listed as processes on the GPU.
- The kernel log shows the 615.71.09 open kernel module, modeset and DRM drivers loading with no errors. The two taint lines, out-of-tree module and missing signature, are expected for an unsigned DKMS module with Secure Boot off.

## Notes

- Driver updates now come with ordinary `apt upgrade` from NVIDIA's repository, and DKMS rebuilds the module for each new kernel.
- If Secure Boot is turned on later, the module has to be signed with an enrolled MOK, or it will not load.
- After the reboot, `systemctl --failed` lists `hostapd-wpe`, `isc-dhcp-server` and `sslh`. These are Parrot tool services that fail without configuration, and they are unrelated to the driver. I left them alone.
