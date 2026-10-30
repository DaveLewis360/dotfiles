/* blur-shim.c — visszaállítja a Hyprland blur-t a Ghostty mögé.
 *
 * A wl_registry események közül kiszűrjük az ext_background_effect_manager_v1
 * globált (a GTK4 üres blur-régiója miatt a Hyprland kihagyná a blur-t),
 * de KIZÁRÓLAG a ghostty saját folyamatában és KIZÁRÓLAG a kliens által
 * regisztrált wl_registry listener-ekben.
 *
 * Fontos tanulságok (ezért ilyen bonyolult):
 *   1. A LD_PRELOAD a ghostty gyermekeire (zsh, fastfetch, stb.) is
 *      átöröklődik — ezért a szűrés /proc/self/comm alapján csak ghosttyban
 *      aktív (a fastfetch saját wl_registry-kezelése így hibátlan).
 *   2. A shim SOHA ne linkeljen libwayland-et: a preload-ként betöltött
 *      libwayland más symbol-resolver sorrendet okoz, és a libwayland belső
 *      wl_proxy_add_listener-hivatkozásai elbuknak (a fastfetch dlopen-os
 *      használatánál a registry-figyelő nem áll fel → végtelen várakozás).
 *      Minden libwayland-függvényt dlopen(NOLOAD)+dlsym oldunk meg, és a
 *      libwayland-ből érkező belső hívásokat dladdr alapján átengedjük.
 *
 * Fordítás (LIBWAYLAND NÉLKÜL!):
 *   cc -O2 -shared -fPIC -o ~/.local/lib/libghostty-blur-shim.so blur-shim.c -ldl
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define FILTERED_GLOBAL "ext_background_effect_manager_v1"

/* Minimal Wayland-deklarációk — szándékosan nem a wayland-client.h-ból,
 * hogy ne kelljen linkelnünk a libwayland-et. */
struct wl_proxy;
struct wl_registry;
struct wl_interface {
    const char *name; /* csak az első mezőt használjuk */
};

/* A wl_registry_listener két függvénypointere — a wayland-client.h helyett. */
struct wl_registry_listener {
    void (*global)(void *data, struct wl_registry *registry, uint32_t name,
                   const char *interface, uint32_t version);
    void (*global_remove)(void *data, struct wl_registry *registry, uint32_t name);
};

typedef int (*fn_add_listener)(struct wl_proxy *, void (**)(void), void *);
typedef const struct wl_interface *(*fn_get_iface)(struct wl_proxy *);

static fn_add_listener real_add_listener  = NULL;
static fn_get_iface    real_get_interface = NULL;

/* A valódi függvényeket csak akkor keressük, ha már betöltődött a
 * libwayland (NOLOAD): soha ne töltsük be mi, és ne használjunk
 * RTLD_NEXT-et (dlopen-os sorrendben az megbízhatatlan). */
static void resolve_wayland(void)
{
    if (real_add_listener)
        return;
    void *h = dlopen("libwayland-client.so.0", RTLD_LAZY | RTLD_NOLOAD);
    if (!h)
        h = dlopen("libwayland-client.so", RTLD_LAZY | RTLD_NOLOAD);
    if (h) {
        real_add_listener  = (fn_add_listener)dlsym(h, "wl_proxy_add_listener");
        real_get_interface = (fn_get_iface)dlsym(h, "wl_proxy_get_interface");
    }
}

/* A shim csak a ghostty saját folyamatában szűr. */
static int is_ghostty(void)
{
    static int cached = -1;
    if (cached == -1) {
        char buf[64] = {0};
        int  fd      = open("/proc/self/comm", O_RDONLY | O_CLOEXEC);
        if (fd >= 0) {
            (void)!read(fd, buf, sizeof(buf) - 1);
            close(fd);
        }
        cached = strncmp(buf, "ghostty", 7) == 0 ? 1 : 0;
    }
    return cached;
}

struct listener_wrap {
    void (*impl[2])(void); /* global, global_remove */
    void *data;
};

static void wrap_global(void *data, struct wl_registry *registry, uint32_t name,
                        const char *interface, uint32_t version)
{
    struct listener_wrap *w = data;

    /* A szűrt globált egyszerűen nem továbbítjuk a kliensnek. */
    if (strcmp(interface, FILTERED_GLOBAL) == 0)
        return;

    ((void (*)(void *, struct wl_registry *, uint32_t, const char *, uint32_t))w->impl[0])(
        w->data, registry, name, interface, version);
}

static void wrap_global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
    struct listener_wrap *w = data;
    ((void (*)(void *, struct wl_registry *, uint32_t))w->impl[1])(w->data, registry, name);
}

static const struct wl_registry_listener wrapped_registry_listener = {
    .global        = wrap_global,
    .global_remove = wrap_global_remove,
};

int wl_proxy_add_listener(struct wl_proxy *proxy, void (**implementation)(void), void *data)
{
    resolve_wayland();
    if (!real_add_listener)
        return -1;

    /* Ha debug kell: GHOSTTY_BLUR_SHIM_DEBUG=1 */
    if (getenv("GHOSTTY_BLUR_SHIM_DEBUG")) {
        char    comm[64] = {0};
        int     cfd      = open("/proc/self/comm", O_RDONLY | O_CLOEXEC);
        Dl_info cinfo    = {0};
        const char *from = "?";
        if (cfd >= 0) {
            (void)!read(cfd, comm, sizeof(comm) - 1);
            close(cfd);
        }
        if (dladdr(__builtin_return_address(0), &cinfo) && cinfo.dli_fname)
            from = cinfo.dli_fname;
        fprintf(stderr, "[shim] comm=%s hivo=%s\n", comm, from);
    }

    /* A libwayland belső hívásait (pl. a saját dispatcher-felállítás) soha
     * ne módosítsuk — ezek nem a kliens registry-figyelői. */
    {
        Dl_info cinfo = {0};
        if (dladdr(__builtin_return_address(0), &cinfo) && cinfo.dli_fname &&
            strstr(cinfo.dli_fname, "libwayland"))
            return real_add_listener(proxy, implementation, data);
    }

    /* Nem a ghostty folyamatában vagyunk → semmit sem szűrünk. */
    if (!is_ghostty())
        return real_add_listener(proxy, implementation, data);

    const struct wl_interface *iface =
        real_get_interface ? real_get_interface(proxy) : NULL;

    /* Csak a wl_registry-éket csomagoljuk körbe, mindent más változatlanul megy. */
    if (iface && iface->name && strcmp(iface->name, "wl_registry") == 0 && implementation) {
        struct listener_wrap *w = malloc(sizeof(*w));
        if (w) {
            w->impl[0] = implementation[0];
            w->impl[1] = implementation[1];
            w->data    = data;
            return real_add_listener(proxy, (void (**)(void))&wrapped_registry_listener, w);
        }
    }

    return real_add_listener(proxy, implementation, data);
}
