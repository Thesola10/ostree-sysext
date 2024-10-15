# <img src="https://raw.githubusercontent.com/thesola10/ostree-sysext/master/.github/icon.svg" width="64"></img> ostree-sysext

## DISCLAIMER

ostree-sysext is currently alpha software, provided as-is with no guarantee.

---

`ostree-sysext` is a frontend built on top of [OSTree](https://github.com/ostreedev/ostree) and `systemd`'s [System Extension Images](https://www.freedesktop.org/software/systemd/man/latest/systemd-sysext.html).

## Design

`ostree-sysext` is designed around system extensions, as defined by the [`systemd-sysext`](https://www.freedesktop.org/software/systemd/man/latest/systemd-sysext.html) tool. Much like Flatpak, it allows system extensions to be retrieved using OSTree remotes.

