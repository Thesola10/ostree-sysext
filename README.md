# <img src="https://raw.githubusercontent.com/thesola10/ostree-sysext/master/.github/icon.svg" width="64"></img> ostree-sysext

## DISCLAIMER

ostree-sysext is currently alpha software, provided as-is with no guarantee.

> [!WARNING]
> Not everything is implemented! I encourage you to check out [the wiki](https://github.com/thesola10/ostree-sysext/wiki) for the intended design.

---

`ostree-sysext` is a frontend built on top of [OSTree](https://github.com/ostreedev/ostree) and `systemd`'s [`systemd-sysext` tool](https://www.freedesktop.org/software/systemd/man/latest/systemd-sysext.html).

## Design

`ostree-sysext` is designed around system extensions, as defined by the [UAPI specification](https://uapi-group.org/specifications/specs/extension_image/). Much like Flatpak, it allows system extensions to be retrieved using OSTree remotes.

Additionally, `ostree-sysext` provides a plugin framework for vendors:

### Builders

Builders intervene on an individual extension, and allow the extension to be created and updated locally, using sources from outside `ostree-sysext`, like a traditional package manager.

### Plugins

Plugins intervene once the full set of plugins for a system is being merged. They can vote on whether the set is feasible, such as with package conflicts.

They can also generate files that depend on the full set of plugins, such as the initramfs or a package manager database. Those files are then available in `/run/ostree/extensions/state`, which image vendors can point symbolic links to in their system image.
