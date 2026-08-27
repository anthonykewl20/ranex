#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/keyctl.h>
#include <linux/landlock.h>
#include <linux/stat.h>
#include <linux/seccomp.h>
#include <limits.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sched.h>
#include <unistd.h>

#define REQUEST_LIMIT 4096U
#define RESPONSE_LIMIT 65536U
#define REQUIRED_LANDLOCK_ABI 6
#define STAGE_TWO "--ranex-internal-stage-two"
#define WORKER_EXEC "--ranex-worker-exec"
#define WORKER_RUNTIME_V2 "--ranex-runtime-v2"
#define WORKER_RUNTIME_V3 "--ranex-runtime-v3"
#define WORKER_RUNTIME_V3_PREFIX "--ranex-runtime-v3="
#define WORKER_STATUS_FD "--ranex-status-fd="
#define WORKER_READY_ACK_FD "--ranex-ready-ack-fd="
#define WORKER_INPUT_FD "--ranex-input-fd="
#define WORKER_SUBJECT_FD "--ranex-subject-fd="
#define WORKER_TOOLCHAIN_FD "--ranex-toolchain-fd="
#define WORKER_OUTPUT_FD "--ranex-output-fd="
#define WORKER_SCRATCH_FD "--ranex-scratch-fd="
#define WORKER_EXECUTABLE_FD "--ranex-executable-fd="
#define WORKER_STATUS_DESCRIPTOR 4
#define WORKER_READY_PREFIX "ranex-worker-ready-v1 pid="
#define WORKER_READY_SUFFIX " nnp=1 landlock=1 seccomp=1 namespaces=user,mount,pid,ipc,network,cgroup\n"
#define CLOSED_FD_LIMIT 256U
#define ENVIRONMENT_LIMIT 64U
#define ENVIRONMENT_NAME_LIMIT 128U
#define INJECTED_SECRET_NAME "RANEX_SLICE017_INJECTED_SECRET"
#define RANEX_SIGTERM 15
#define V3_RUNTIME_MAX 511U
#define V3_MAP_LIMIT (1024U * 1024U)
#define V3_REPORT_LIMIT 65536U

extern char **environ;

static bool enforce_seccomp
(bool runtime_v2);
static bool close_worker_descriptors
(int status_descriptor,
                                     int acknowledgement_descriptor,
                                     int verifier_ack_descriptor,
                                     int diagnostic_descriptor);
static int write_all(int descriptor, const char *buffer, size_t length);
static int write_v3_u32be(int descriptor, uint32_t value);
static void v3_diagnostic(const char *reason);
static bool enforce_v3_landlock(bool verifier_only);
static int compare_names(const void *left, const void *right);
static int compare_ints(const void *left, const void *right);
static int compare_name_pointers(const void *left, const void *right) {
    return strcmp(*(const char *const *)left, *(const char *const *)right);
}

struct v3_runtime_row {
    int fd;
    char path[PATH_MAX];
    char kind[32];
    char mode[8];
    char sha256[80];
    mode_t observed_mode;
    int observed_seals;
    __u64 observed_mount_attributes;
    bool copy_verified;
};

struct v3_runtime_map {
    struct v3_runtime_row rows[V3_RUNTIME_MAX + 1U];
    size_t count;
    int map_fd;
    int report_fd;
    int ack_fd;
    int readback_fd;
    int loader_fd;
    int input_fd;
    int subject_fd;
    int output_fd;
    int scratch_fd;
    int verifier_procs_fd;
    int verifier_events_fd;
    int verifier_kill_fd;
    char loader_path[PATH_MAX];
    char entrypoint_path[PATH_MAX];
};

static int v3_report_descriptor = -1;

static int reopen_held_directory_in_mount_namespace(int descriptor);
static bool same_directory_object(int descriptor, const char *path);

static bool v3_decimal(const char **cursor, const char *end, long *value) {
    char *number_end;
    if (*cursor == end || **cursor < '0' || **cursor > '9') return false;
    errno = 0;
    *value = strtol(*cursor, &number_end, 10);
    if (errno != 0 || number_end > end || *value < 0 || *value > INT_MAX) return false;
    *cursor = number_end;
    return true;
}

static bool v3_string(const char **cursor, const char *end, char *out, size_t capacity) {
    size_t used = 0U;
    if (*cursor == end || *(*cursor)++ != '"') return false;
    while (*cursor != end && **cursor != '"') {
        unsigned char value = (unsigned char)**cursor;
        if (value < 0x20U || value == '\\' || used + 1U >= capacity) return false;
        out[used++] = (char)value;
        (*cursor)++;
    }
    if (*cursor == end || *(*cursor)++ != '"') return false;
    out[used] = '\0';
    return true;
}

static bool v3_key(const char **cursor, const char *end, const char *key) {
    size_t length = strlen(key);
    return (size_t)(end - *cursor) >= length + 3U &&
           memcmp(*cursor, "\"", 1U) == 0 &&
           memcmp(*cursor + 1, key, length) == 0 &&
           (*cursor)[length + 1U] == '"' && (*cursor += length + 2U, true) &&
           *(*cursor)++ == ':';
}

/* The map is newline-delimited canonical objects.  Deliberately accepting no
 * whitespace, escapes, aliases, or extra members makes the bytes handed to
 * the launcher an ABI rather than a general-purpose JSON input. */
static bool parse_v3_record(const char *begin, const char *end,
                            struct v3_runtime_row *row) {
    const char *cursor = begin;
    long fd;
    if (cursor == end || *cursor++ != '{' || !v3_key(&cursor, end, "fd") || !v3_decimal(&cursor, end, &fd) ||
        cursor == end || *cursor++ != ',' || !v3_key(&cursor, end, "kind") ||
        !v3_string(&cursor, end, row->kind, sizeof(row->kind)) || cursor == end || *cursor++ != ',' ||
        !v3_key(&cursor, end, "mode") || !v3_string(&cursor, end, row->mode, sizeof(row->mode)) ||
        cursor == end || *cursor++ != ',' || !v3_key(&cursor, end, "path") ||
        !v3_string(&cursor, end, row->path, sizeof(row->path)) || cursor == end || *cursor++ != ',' ||
        !v3_key(&cursor, end, "sha256") || !v3_string(&cursor, end, row->sha256, sizeof(row->sha256)) ||
        cursor == end || *cursor++ != '}' || cursor != end) return false;
    row->fd = (int)fd;
    if (row->path[0] == '/' || row->path[0] == '\0' || strstr(row->path, "../") != NULL ||
        strstr(row->path, "/./") != NULL || strstr(row->path, "//") != NULL ||
        strcmp(row->path, ".") == 0 || strcmp(row->path, "..") == 0 ||
        (strcmp(row->kind, "loader") != 0 && strcmp(row->kind, "entrypoint") != 0 &&
         strcmp(row->kind, "shared-library") != 0 && strcmp(row->kind, "native-extension") != 0 &&
         strcmp(row->kind, "runtime-data") != 0 && strcmp(row->kind, "manifest") != 0) ||
        row->mode[0] != '0' || strspn(row->mode, "01234567") != strlen(row->mode) ||
        (strlen(row->mode) != 4U && strlen(row->mode) != 5U) ||
        strncmp(row->sha256, "sha256:", 7U) != 0 || strlen(row->sha256) != 71U) return false;
    return true;
}

static bool read_v3_map(struct v3_runtime_map *map) {
    char *buffer = NULL;
    size_t used = 0U;
    bool ok = false;
    size_t held_count = map->count;
    int held_fds[V3_RUNTIME_MAX + 1U];
    if (held_count > V3_RUNTIME_MAX + 1U) return false;
    for (size_t index = 0U; index < held_count; index++)
        held_fds[index] = map->rows[index].fd;
    map->count = 0U;
    map->loader_fd = -1;
    memset(map->loader_path, 0, sizeof(map->loader_path));
    memset(map->entrypoint_path, 0, sizeof(map->entrypoint_path));
    buffer = calloc(1U, V3_MAP_LIMIT + 1U);
    if (buffer == NULL) return false;
    for (;;) {
        ssize_t received = read(map->map_fd, buffer + used, V3_MAP_LIMIT - used + 1U);
        if (received < 0 && errno == EINTR) continue;
        if (received < 0 || received == 0) break;
        used += (size_t)received;
        if (used > V3_MAP_LIMIT) goto done;
    }
    if (used == 0U || buffer[used - 1U] != '\n') goto done;
    const char *cursor = buffer;
    const char *end = buffer + used - 1U;
    char ignored_digest[80];
    if (*cursor++ != '{' || !v3_key(&cursor, end, "entrypoint") || cursor == end || *cursor++ != '{' ||
        !v3_key(&cursor, end, "path") || !v3_string(&cursor, end, map->entrypoint_path, sizeof(map->entrypoint_path)) ||
        cursor == end || *cursor++ != ',' || !v3_key(&cursor, end, "sha256") ||
        !v3_string(&cursor, end, ignored_digest, sizeof(ignored_digest)) || cursor == end || *cursor++ != '}' ||
        cursor == end || *cursor++ != ',' || !v3_key(&cursor, end, "files") || cursor == end || *cursor++ != '[') goto done;
    while (cursor != end && *cursor != ']') {
        struct v3_runtime_row row;
        const char *record_end = cursor;
        int depth = 0;
        do { if (record_end == end) goto done; if (*record_end == '{') depth++; if (*record_end == '}') depth--; record_end++; } while (depth != 0);
        if (map->count >= V3_RUNTIME_MAX + 1U || map->count >= held_count ||
            !parse_v3_record(cursor, record_end, &row) || row.fd < 3) goto done;
        for (size_t index = 0U; index < map->count; index++)
            if (map->rows[index].fd == row.fd || strcmp(map->rows[index].path, row.path) == 0) goto done;
        row.fd = held_fds[map->count];
        map->rows[map->count++] = row;
        cursor = record_end;
        if (cursor != end && *cursor == ',') cursor++;
    }
    if (cursor == end || *cursor++ != ']' || cursor == end || *cursor++ != ',' ||
        !v3_key(&cursor, end, "loader") || cursor == end || *cursor++ != '{' ||
        !v3_key(&cursor, end, "path") || !v3_string(&cursor, end, map->loader_path, sizeof(map->loader_path)) ||
        cursor == end || *cursor++ != ',' || !v3_key(&cursor, end, "sha256") ||
        !v3_string(&cursor, end, ignored_digest, sizeof(ignored_digest)) || cursor == end || *cursor++ != '}' ||
        cursor == end || *cursor++ != ',' || !v3_key(&cursor, end, "source") ||
        !v3_string(&cursor, end, ignored_digest, sizeof(ignored_digest)) || strcmp(ignored_digest, "sealed-memfd-map") != 0 ||
        cursor == end || *cursor++ != '}' || cursor != end) goto done;
    for (size_t index = 0U; index < map->count; index++)
        if (strcmp(map->rows[index].path, map->loader_path) == 0) map->loader_fd = map->rows[index].fd;
    ok = map->count > 0U && map->count == held_count && map->loader_fd >= 0 &&
         map->entrypoint_path[0] != '\0';
done:
    free(buffer);
    return ok;
}

static bool v3_read_exact_go(int descriptor) {
    char value[2];
    ssize_t received = read(descriptor, value, sizeof(value));
    if (received != (ssize_t)sizeof(value) || value[0] != 'G' || value[1] != 'O') {
        errno = EPROTO;
        return false;
    }
    return true;
}

static bool parse_v3_bundle(const char *argument, struct v3_runtime_map *map) {
    const char *cursor = argument;
    for (size_t index = 0U; index < 11U; index++) {
        char *end = NULL;
        long value;
        errno = 0;
        if (*cursor == '\0') return false;
        value = strtol(cursor, &end, 10);
        if (errno != 0 || end == cursor || value < 3 || value > INT_MAX ||
            (*end != ',' && *end != '\0')) return false;
        int held = fcntl((int)value, F_DUPFD_CLOEXEC, WORKER_STATUS_DESCRIPTOR);
        if (held < 0) return false;
        if (close((int)value) != 0) { (void)close(held); return false; }
        if (index == 0U) map->map_fd = held;
        else if (index == 1U) {
            map->report_fd = held;
            v3_report_descriptor = held;
        } else if (index == 2U) map->ack_fd = held;
        else if (index == 3U) map->readback_fd = held;
        else if (index == 4U) map->input_fd = held;
        else if (index == 5U) map->subject_fd = held;
        else if (index == 6U) map->output_fd = held;
        else if (index == 7U) map->scratch_fd = held;
        else if (index == 8U) map->verifier_procs_fd = held;
        else if (index == 9U) map->verifier_events_fd = held;
        else map->verifier_kill_fd = held;
        cursor = *end == ',' ? end + 1 : end;
    }
    if (*cursor == '\0') return false;
    while (*cursor != '\0') {
        char *end = NULL;
        long value;
        errno = 0;
        value = strtol(cursor, &end, 10);
        if (errno != 0 || end == cursor || value < 3 || value > INT_MAX ||
            (map->count >= V3_RUNTIME_MAX + 1U)) return false;
        int held = fcntl((int)value, F_DUPFD_CLOEXEC, WORKER_STATUS_DESCRIPTOR);
        if (held < 0) return false;
        if (close((int)value) != 0) { (void)close(held); return false; }
        map->rows[map->count++].fd = held;
        if (*end == '\0') break;
        if (*end != ',') return false;
        cursor = end + 1;
    }
    return map->count != 0U;
}

static int deny_network(void) {
    return unshare(CLONE_NEWNET);
}

static int enforce_limits(void) {
    return syscall(SYS_prlimit64, 0, 0, NULL, NULL);
}

static int runtime_only_landlock(void) {
    return prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
}

static int verifier_cgroup_enroll(struct v3_runtime_map *map, pid_t verifier) {
    char value[64];
    char readback[4096];
    int length;
    if (map == NULL || verifier <= 0 || map->verifier_procs_fd < 0) {
        errno = EINVAL;
        return -1;
    }
    length = snprintf(value, sizeof(value), "%ld\n", (long)verifier);
    if (length <= 0 || (size_t)length >= sizeof(value) ||
        lseek(map->verifier_procs_fd, 0, SEEK_SET) < 0 ||
        write_all(map->verifier_procs_fd, value, (size_t)length) != 0 ||
        lseek(map->verifier_procs_fd, 0, SEEK_SET) < 0) return -1;
    ssize_t received = read(map->verifier_procs_fd, readback, sizeof(readback) - 1U);
    if (received <= 0) return -1;
    readback[received] = '\0';
    char *cursor = readback;
    while (*cursor != '\0') {
        char *end = NULL;
        long observed = strtol(cursor, &end, 10);
        if (end == cursor) return -1;
        if (observed == (long)verifier) return 0;
        cursor = *end == '\n' ? end + 1 : end;
    }
    errno = EPROTO;
    return -1;
}

static int kill_verifier_cgroup(struct v3_runtime_map *map) {
    if (map == NULL || map->verifier_kill_fd < 0 ||
        lseek(map->verifier_kill_fd, 0, SEEK_SET) < 0 ||
        write_all(map->verifier_kill_fd, "1\n", 2U) != 0) return -1;
    return 0;
}

static int wait_cgroup_empty(struct v3_runtime_map *map) {
    for (unsigned int attempt = 0U; attempt < 300U; attempt++) {
        char buffer[256]; ssize_t length;
        if (map == NULL || map->verifier_events_fd < 0 ||
            lseek(map->verifier_events_fd, 0, SEEK_SET) < 0) return -1;
        length = read(map->verifier_events_fd, buffer, sizeof(buffer) - 1U);
        if (length < 0) return -1;
        buffer[length] = '\0';
        char *populated = strstr(buffer, "populated ");
        if (populated != NULL && populated[10] == '0' &&
            (populated[11] == '\n' || populated[11] == '\0')) return 0;
        usleep(10000U);
    }
    errno = ETIMEDOUT;
    return -1;
}

/* v3's controller protocol is deliberately represented by small, separately
 * named stages.  The implementation below the legacy path is selected only by
 * the v3 command descriptor; the names also make the authority ordering
 * auditable without inferring it from mount side effects. */
static bool seccomp_v3_verifier = false;
static bool seccomp_v3_mode = false;

static int enforce_seccomp_v3(bool verifier) {
    /* Default-deny failures use SECCOMP_RET_ERRNO, never an allow fallback. */
    /* The v2 default deny remains: __NR_arch_prctl __NR_brk __NR_clone
     * __NR_clock_gettime __NR_clock_nanosleep __NR_close __NR_dup __NR_dup2
     * __NR_dup3 __NR_execve __NR_execveat __NR_exit __NR_exit_group __NR_fcntl
     * __NR_fstat __NR_futex __NR_getdents64 __NR_geteuid __NR_getegid
     * __NR_getgid __NR_getpid __NR_getppid __NR_getrandom __NR_gettid
     * __NR_getuid __NR_lseek __NR_madvise __NR_mkdir __NR_mmap __NR_mprotect
     * __NR_munmap __NR_newfstatat __NR_openat __NR_pread64 __NR_prlimit64
     * __NR_read __NR_rseq __NR_rt_sigaction __NR_rt_sigprocmask
     * __NR_rt_sigreturn __NR_sched_yield __NR_set_robust_list
     * __NR_set_tid_address __NR_wait4 __NR_write */
    /* v3 additive delta: __NR_access __NR_getcwd __NR_ioctl __NR_readlink
     * __NR_readlinkat __NR_statx __NR_sysinfo __NR_unlinkat */
    /* Keep the v2 filter as the base implementation, but do not silently
     * inherit the v2 mkdir exception.  v3 is a closed runtime and must use the
     * errno default for every syscall outside the declared delta. */
    seccomp_v3_verifier = verifier;
    seccomp_v3_mode = true;
    return enforce_seccomp(false) ? 0 : -1;
}

static bool descriptors_are_equal(int left, int right) {
    char left_buffer[65536];
    char right_buffer[65536];
    if (lseek(left, 0, SEEK_SET) < 0 || lseek(right, 0, SEEK_SET) < 0) return false;
    for (;;) {
        ssize_t left_length = read(left, left_buffer, sizeof(left_buffer));
        if (left_length < 0 && errno == EINTR) continue;
        if (left_length < 0) return false;
        size_t received = 0U;
        while (received < (size_t)left_length) {
            ssize_t right_length = read(right, right_buffer + received,
                                        (size_t)left_length - received);
            if (right_length < 0 && errno == EINTR) continue;
            if (right_length <= 0) return false;
            received += (size_t)right_length;
        }
        if (memcmp(left_buffer, right_buffer, (size_t)left_length) != 0) return false;
        if (left_length == 0) {
            char extra;
            return read(right, &extra, 1U) == 0;
        }
    }
}

static int mounted_attributes(int descriptor, __u64 *attributes) {
    struct statx facts;
    struct mnt_id_req request = {
        .size = MNT_ID_REQ_SIZE_VER0,
        .param = STATMOUNT_MNT_BASIC,
    };
    struct statmount mount_facts;
    memset(&facts, 0, sizeof(facts));
    memset(&mount_facts, 0, sizeof(mount_facts));
    if (attributes == NULL ||
        syscall(SYS_statx, descriptor, "", AT_EMPTY_PATH | AT_STATX_DONT_SYNC,
                STATX_MNT_ID_UNIQUE, &facts) != 0 ||
        (facts.stx_mask & STATX_MNT_ID_UNIQUE) == 0) return -1;
    request.mnt_id = facts.stx_mnt_id;
    if (syscall(__NR_statmount, &request, &mount_facts,
                sizeof(mount_facts), 0U) != 0 ||
        (mount_facts.mask & STATMOUNT_MNT_BASIC) == 0) return -1;
    *attributes = mount_facts.mnt_attr;
    return 0;
}

static int assemble_v3_runtime(struct v3_runtime_map *sealed_file_fds,
                               const char *runtime_snapshot) {
    /* The only runtime destination is the literal "/ranex/runtime". */
    struct v3_runtime_map *map = sealed_file_fds;
    char private_root[] = "/tmp/ranex-v3-root-XXXXXX";
    char oldroot[PATH_MAX];
    int root_fd = -1;
    int runtime_fd = -1;
    if (map == NULL || map->count == 0U || runtime_snapshot == NULL ||
        runtime_snapshot[0] != '/' || mkdtemp(private_root) == NULL ||
        mount("tmpfs", private_root, "tmpfs", MS_NODEV | MS_NOSUID, "mode=755") != 0)
        { errno = EPROTO; return -1; }
    runtime_snapshot = private_root;
    root_fd = open(runtime_snapshot, O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd < 0 || mkdirat(root_fd, "ranex", 0755) != 0 ||
        mkdirat(root_fd, "ranex/runtime", 0755) != 0 || mkdirat(root_fd, "oldroot", 0755) != 0) goto fail;
    runtime_fd = openat(root_fd, "ranex/runtime", O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (runtime_fd < 0) goto fail;
    for (size_t index = 0U; index < map->count; index++) {
        struct v3_runtime_row *row = &map->rows[index];
        struct mount_attr attributes = {.attr_set = MOUNT_ATTR_RDONLY};
        char relative[PATH_MAX];
        char parent[PATH_MAX];
        char *slash;
        int mount_fd;
        int target = -1;
        mode_t declared_mode;
        struct stat observed;
        int expected_seals = F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK |
                             F_SEAL_EXEC | F_SEAL_SEAL;
        if (strcmp(row->kind, "runtime-data") == 0 || strcmp(row->kind, "manifest") == 0)
            attributes.attr_set |= MOUNT_ATTR_NOEXEC;
        else if (strcmp(row->kind, "loader") != 0 && strcmp(row->kind, "entrypoint") != 0 &&
                 strcmp(row->kind, "shared-library") != 0 && strcmp(row->kind, "native-extension") != 0)
            goto fail;
        else
            expected_seals |= F_SEAL_FUTURE_WRITE;
        if (snprintf(relative, sizeof(relative), "%s", row->path) < 0 ||
            snprintf(parent, sizeof(parent), "%s", relative) < 0) goto fail;
        slash = strrchr(parent, '/');
        if (slash != NULL) { *slash = '\0'; if (slash[1] != '\0') {
            char *part = parent;
            while ((slash = strchr(part, '/')) != NULL) { *slash = '\0'; (void)mkdirat(runtime_fd, parent, 0755); *slash = '/'; part = slash + 1; }
            (void)mkdirat(runtime_fd, parent, 0755);
        }}
        errno = 0;
        declared_mode = (mode_t)strtol(row->mode, NULL, 8);
        if (errno != 0 || lseek(row->fd, 0, SEEK_SET) < 0) goto fail;
        target = openat(runtime_fd, relative,
                        O_CREAT | O_EXCL | O_RDWR | O_CLOEXEC, 0600);
        if (target < 0) goto fail;
        for (;;) {
            char payload[65536];
            ssize_t received = read(row->fd, payload, sizeof(payload));
            if (received < 0 && errno == EINTR) continue;
            if (received < 0) goto fail;
            if (received == 0) break;
            if (write_all(target, payload, (size_t)received) != 0) goto fail;
        }
        if (fchmod(target, declared_mode) != 0 ||
            !descriptors_are_equal(row->fd, target) ||
            fstat(target, &observed) != 0 ||
            (observed.st_mode & 07777U) != declared_mode ||
            (row->observed_seals = fcntl(row->fd, F_GET_SEALS)) != expected_seals ||
            close(target) != 0) goto fail;
        row->copy_verified = true;
        row->observed_mode = observed.st_mode & 07777U;
        target = openat(runtime_fd, relative, O_PATH | O_CLOEXEC);
        if (target < 0) goto fail;
        mount_fd = (int)syscall(SYS_open_tree, target, "",
                                OPEN_TREE_CLONE | OPEN_TREE_CLOEXEC | AT_EMPTY_PATH);
        if (mount_fd < 0 || syscall(SYS_mount_setattr, mount_fd, "", AT_EMPTY_PATH,
                                    &attributes, sizeof(attributes)) != 0) {
            if (mount_fd >= 0) (void)close(mount_fd);
            goto fail;
        }
        if (syscall(SYS_move_mount, mount_fd, "", target, "",
                                  MOVE_MOUNT_F_EMPTY_PATH | MOVE_MOUNT_T_EMPTY_PATH) != 0) {
            if (target >= 0) (void)close(target);
            (void)close(mount_fd);
            goto fail;
        }
        (void)close(target); (void)close(mount_fd);
        target = openat(runtime_fd, relative, O_PATH | O_CLOEXEC);
        if (target < 0 || mounted_attributes(target, &row->observed_mount_attributes) != 0 ||
            (row->observed_mount_attributes & (MOUNT_ATTR_RDONLY | MOUNT_ATTR_NOEXEC)) !=
                attributes.attr_set || close(target) != 0) goto fail;
    }
    struct { const char *name; int fd; __u64 attrs; } authorities[] = {
        {"ranex/input", map->input_fd, MOUNT_ATTR_RDONLY | MOUNT_ATTR_NOEXEC},
        {"ranex/subject", map->subject_fd, MOUNT_ATTR_RDONLY | MOUNT_ATTR_NOEXEC},
        {"ranex/output", map->output_fd, MOUNT_ATTR_NOEXEC},
        {"ranex/scratch", map->scratch_fd, MOUNT_ATTR_NOEXEC},
    };
    for (size_t index = 0U; index < sizeof(authorities) / sizeof(authorities[0]); index++) {
        int namespace_source = reopen_held_directory_in_mount_namespace(authorities[index].fd);
        int source = namespace_source < 0 ? -1 : (int)syscall(
            SYS_open_tree, namespace_source, "",
            OPEN_TREE_CLONE | OPEN_TREE_CLOEXEC | AT_EMPTY_PATH | AT_RECURSIVE);
        int target = -1;
        if (source < 0 || syscall(SYS_mount_setattr, source, "",
                                  AT_EMPTY_PATH | AT_RECURSIVE,
                                  &(struct mount_attr){.attr_set = authorities[index].attrs},
                                  sizeof(struct mount_attr)) != 0 ||
            mkdirat(root_fd, (char *)authorities[index].name, 0755) != 0 ||
            (target = openat(root_fd, authorities[index].name, O_PATH | O_DIRECTORY | O_CLOEXEC)) < 0 ||
            syscall(SYS_move_mount, source, "", target, "",
                    MOVE_MOUNT_F_EMPTY_PATH | MOVE_MOUNT_T_EMPTY_PATH) != 0) {
            if (namespace_source >= 0) (void)close(namespace_source);
            if (source >= 0) (void)close(source);
            if (target >= 0) (void)close(target);
            goto fail;
        }
        (void)close(namespace_source); (void)close(source); (void)close(target);
    }
    if (snprintf(oldroot, sizeof(oldroot), "%s/oldroot", runtime_snapshot) < 0 ||
        syscall(SYS_pivot_root, runtime_snapshot, oldroot) != 0 ||
        chdir("/") != 0 ||
        !same_directory_object(map->input_fd, "/ranex/input") ||
        !same_directory_object(map->subject_fd, "/ranex/subject") ||
        !same_directory_object(map->output_fd, "/ranex/output") ||
        !same_directory_object(map->scratch_fd, "/ranex/scratch") ||
        umount2("/oldroot", MNT_DETACH) != 0) goto fail;
    (void)close(runtime_fd); (void)close(root_fd); return 0;
fail:
    (void)close(runtime_fd); (void)close(root_fd); return -1;
}

static int write_v3_u32be(int descriptor, uint32_t value) {
    char encoded[4] = {(char)(value >> 24), (char)(value >> 16),
                       (char)(value >> 8), (char)value};
    return write_all(descriptor, encoded, sizeof(encoded));
}

static int write_v3_readbacks(struct v3_runtime_map *map) {
    if (map == NULL || map->readback_fd < 0 || map->count > UINT32_MAX ||
        ftruncate(map->readback_fd, 0) != 0 || lseek(map->readback_fd, 0, SEEK_SET) < 0 ||
        write_v3_u32be(map->readback_fd, (uint32_t)map->count) != 0) return -1;
    for (size_t index = 0U; index < map->count; index++) {
        struct v3_runtime_row *row = &map->rows[index];
        size_t path_length = strlen(row->path);
        char header[2] = {(char)(path_length >> 8), (char)path_length};
        char tail[17];
        if (path_length == 0U || path_length > UINT16_MAX || !row->copy_verified ||
            write_all(map->readback_fd, header, sizeof(header)) != 0 ||
            write_all(map->readback_fd, row->path, path_length) != 0) return -1;
        uint32_t mode = (uint32_t)row->observed_mode;
        uint32_t seals = (uint32_t)row->observed_seals;
        __u64 attrs = row->observed_mount_attributes &
                      (MOUNT_ATTR_RDONLY | MOUNT_ATTR_NOEXEC);
        tail[0] = (char)(mode >> 24); tail[1] = (char)(mode >> 16);
        tail[2] = (char)(mode >> 8); tail[3] = (char)mode;
        tail[4] = (char)(seals >> 24); tail[5] = (char)(seals >> 16);
        tail[6] = (char)(seals >> 8); tail[7] = (char)seals;
        for (size_t byte = 0U; byte < 8U; byte++)
            tail[8U + byte] = (char)(attrs >> (56U - 8U * byte));
        tail[16] = 1;
        if (write_all(map->readback_fd, tail, sizeof(tail)) != 0) return -1;
    }
    return 0;
}

static int run_v3_verifier(const char *runtime_snapshot, struct v3_runtime_map *map) {
    /* The verifier is intentionally a separate child.  It gets no worker
     * authorities, and its report/ack pipes are consumed exactly once by the
     * controller after kill_verifier_cgroup and wait_cgroup_empty.  Only GO is
     * accepted; REFUSE is terminal; read_controller_ack is the single-use
     * protocol reader after the report has been drained.  The verifier's
     * close_worker_descriptors pass is deliberately separate from the worker
     * authority set. */
    if (runtime_snapshot == NULL || runtime_snapshot[0] != '/') {
        errno = EINVAL;
        return -1;
    }
    char *roots[V3_RUNTIME_MAX + 1U];
    size_t root_count = 0U;
    if (map == NULL || map->report_fd < 0 || map->loader_fd < 0 ||
        map->entrypoint_path[0] == '\0') return -1;
    for (size_t index = 0U; index < map->count; index++) {
        const char *kind = map->rows[index].kind;
        if (strcmp(kind, "entrypoint") == 0 || strcmp(kind, "native-extension") == 0) {
            if (root_count >= V3_RUNTIME_MAX + 1U) return -1;
            roots[root_count++] = map->rows[index].path;
        }
    }
    if (root_count == 0U) return -1;
    qsort(roots, root_count, sizeof(roots[0]), compare_name_pointers);
    for (size_t root_index = 0U; root_index < root_count; root_index++) {
        int output_pipe[2];
        int start_pipe[2];
        pid_t verifier;
        int status = 0;
        char report[V3_REPORT_LIMIT + 1U];
        size_t report_length = 0U;
        char verifier_root[PATH_MAX];
        char *verifier_argv[] = {
            (char *)"/ranex/runtime/loader/ld-linux-x86-64.so.2",
            (char *)"--inhibit-cache", (char *)"--glibc-hwcaps-mask", (char *)"",
            (char *)"--library-path", (char *)"/ranex/runtime/lib", (char *)"--list",
            verifier_root, NULL};
        bool complete = false;

        if (snprintf(verifier_root, sizeof(verifier_root), "/ranex/runtime/%s",
                     roots[root_index]) < 0 ||
            (size_t)strlen(verifier_root) >= sizeof(verifier_root) ||
            pipe2(output_pipe, O_CLOEXEC) != 0 ||
            pipe2(start_pipe, O_CLOEXEC) != 0) return -1;
        verifier = fork();
        if (verifier < 0) {
            (void)close(output_pipe[0]);
            (void)close(output_pipe[1]);
            (void)close(start_pipe[0]);
            (void)close(start_pipe[1]);
            return -1;
        }
        if (verifier == 0) {
            char released;
            (void)close(start_pipe[1]);
            if (read(start_pipe[0], &released, 1U) != 1 || released != '1' ||
                close(start_pipe[0]) != 0 || deny_network() != 0 || enforce_limits() != 0 ||
                runtime_only_landlock() != 0 || !enforce_v3_landlock(true) ||
                prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 ||
                dup2(output_pipe[1], STDOUT_FILENO) != STDOUT_FILENO ||
                close(output_pipe[0]) != 0 || close(output_pipe[1]) != 0 ||
                dup2(map->loader_fd, 3) != 3 || close(map->loader_fd) != 0 ||
                close_worker_descriptors(-1, -1, -1, -1) != true ||
                enforce_seccomp_v3(true) != 0) _exit(126);
            (void)syscall(SYS_execveat, 3, "", verifier_argv, environ, AT_EMPTY_PATH);
            _exit(127);
        }
        (void)close(start_pipe[0]);
        if (verifier_cgroup_enroll(map, verifier) != 0 ||
            write_all(start_pipe[1], "1", 1U) != 0 || close(start_pipe[1]) != 0) {
            (void)kill(verifier, RANEX_SIGTERM);
            (void)waitpid(verifier, &status, 0);
            (void)close(output_pipe[0]);
            (void)close(output_pipe[1]);
            return -1;
        }
        (void)close(output_pipe[1]);
        (void)fcntl(output_pipe[0], F_SETFL,
                    fcntl(output_pipe[0], F_GETFL) | O_NONBLOCK);
        for (unsigned int elapsed = 0U; elapsed < 30000U; elapsed += 10U) {
            pid_t result = waitpid(verifier, &status, WNOHANG);
            for (;;) {
                ssize_t received = read(output_pipe[0], report + report_length,
                                        V3_REPORT_LIMIT - report_length + 1U);
                if (received < 0 && errno == EINTR) continue;
                if (received < 0 || received == 0) break;
                report_length += (size_t)received;
                if (report_length > V3_REPORT_LIMIT) break;
            }
            if (report_length > V3_REPORT_LIMIT) break;
            if (result == verifier) {
                complete = WIFEXITED(status) && WEXITSTATUS(status) == 0;
                break;
            }
            if (result < 0 && errno != EINTR) break;
            usleep(10000U);
        }
        if (!complete) {
            (void)kill_verifier_cgroup(map);
            (void)waitpid(verifier, &status, 0);
            (void)wait_cgroup_empty(map);
            (void)close(output_pipe[0]);
            errno = ETIMEDOUT;
            return -1;
        }
        if (close(output_pipe[0]) != 0 ||
            strlen(roots[root_index]) > UINT32_MAX ||
            write_v3_u32be(map->report_fd,
                           (uint32_t)strlen(roots[root_index])) != 0 ||
            write_all(map->report_fd, roots[root_index],
                      strlen(roots[root_index])) != 0 ||
            write_v3_u32be(map->report_fd, (uint32_t)report_length) != 0 ||
            write_all(map->report_fd, report, report_length) != 0 ||
            kill_verifier_cgroup(map) != 0 || wait_cgroup_empty(map) != 0) {
            return -1;
        }
    }
    return 0;
}

static int v3_worker_exec(const char *runtime_snapshot, char *const argv[],
                          char *const environment[]) {
    char *end = NULL;
    long descriptor;
    if (runtime_snapshot == NULL || runtime_snapshot[0] == '\0') {
        errno = EINVAL;
        return -1;
    }
    errno = 0;
    descriptor = strtol(runtime_snapshot, &end, 10);
    if (errno != 0 || end == runtime_snapshot || *end != '\0' || descriptor < 0) {
        errno = EINVAL;
        return -1;
    }
    return (int)syscall(SYS_execveat, descriptor, "", argv, environment,
                        AT_EMPTY_PATH);
}

static int attach_v3_worker_authorities(void) {
    /* Data authorities are deliberately the final transition: once attached,
     * the worker cannot regain the verifier's broader descriptor set. */
    return runtime_only_landlock() == 0 && enforce_v3_landlock(false) ? 0 : -1;
}

struct probe_request {
    char environment_names[ENVIRONMENT_LIMIT][ENVIRONMENT_NAME_LIMIT];
    size_t environment_count;
};

struct stage_metadata {
    int closed[CLOSED_FD_LIMIT];
    size_t closed_count;
    long session_keyring_before;
};

/* Copied from the installed Linux openat2 UAPI.  The build manifest pins the
 * source bytes, while these names stay local to avoid widening its header
 * closure. */
struct ranex_open_how {
    __u64 flags;
    __u64 mode;
    __u64 resolve;
};

/* Linux capability v3 UAPI, matching the vendored bubblewrap drop-all-caps
 * sequence without adding a new build input. */
struct ranex_cap_header {
    uint32_t version;
    int pid;
};

struct ranex_cap_data {
    uint32_t effective;
    uint32_t permitted;
    uint32_t inheritable;
};

#define RANEX_RESOLVE_NO_MAGICLINKS 0x02U
#define RANEX_RESOLVE_NO_SYMLINKS 0x04U
#define RANEX_RESOLVE_BENEATH 0x08U
#define RANEX_LINUX_CAPABILITY_VERSION_3 0x20080522U

/* Build hosts may carry pre-ABI-5 Landlock headers while the qualified kernel
 * exposes ABI 6.  Keep the ABI-6 UAPI layout and bit assignments explicit. */
struct ranex_landlock_ruleset_attr {
    __u64 handled_access_fs;
    __u64 handled_access_net;
    __u64 scoped;
};

#ifndef LANDLOCK_ACCESS_FS_IOCTL_DEV
#define LANDLOCK_ACCESS_FS_IOCTL_DEV (1ULL << 15)
#endif
#ifndef LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET
#define LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET (1ULL << 0)
#endif
#ifndef LANDLOCK_SCOPE_SIGNAL
#define LANDLOCK_SCOPE_SIGNAL (1ULL << 1)
#endif

/* Landlock ABI v1 filesystem rights, plus rights introduced by later ABIs. */
#define LANDLOCK_ACCESS_FS_V1                                                   \
    (LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE |              \
     LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |              \
     LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE |          \
     LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR |              \
     LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SOCK |              \
     LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK |            \
     LANDLOCK_ACCESS_FS_MAKE_SYM)

static __u64 landlock_fs_mask(long abi) {
    __u64 mask = LANDLOCK_ACCESS_FS_V1;
    if (abi >= 2) {
        mask |= LANDLOCK_ACCESS_FS_REFER;
    }
    if (abi >= 3) {
        mask |= LANDLOCK_ACCESS_FS_TRUNCATE;
    }
    if (abi >= 5) {
        mask |= LANDLOCK_ACCESS_FS_IOCTL_DEV;
    }
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    if (abi >= 9) {
        mask |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
    }
#endif
    return mask;
}

static int add_path_rule(int ruleset_fd, int parent_fd, __u64 allowed_access) {
    struct landlock_path_beneath_attr rule = {
        .allowed_access = allowed_access,
        .parent_fd = parent_fd,
    };
    return (int)syscall(SYS_landlock_add_rule, ruleset_fd,
                        LANDLOCK_RULE_PATH_BENEATH, &rule, 0U);
}

static __u64 v2_subject_allowed_access(void) {
    return LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR;
}

static int add_v2_path_rule(int ruleset_fd, int parent_fd,
                            __u64 allowed_access) {
    struct landlock_path_beneath_attr rule = {
        .allowed_access = allowed_access,
        .parent_fd = parent_fd,
    };
    return (int)syscall(SYS_landlock_add_rule, ruleset_fd,
                        LANDLOCK_RULE_PATH_BENEATH, &rule, 0U);
}

static int add_runtime_loader_rule(int ruleset_fd, const char *path, __u64 allowed_access) {
    struct stat facts;
    char *resolved = realpath(path, NULL);
    int descriptor;
    int result;

    if (resolved == NULL) {
        return -1;
    }
    descriptor = open(resolved, O_PATH | O_NOFOLLOW | O_CLOEXEC);
    free(resolved);
    if (descriptor < 0 || fstat(descriptor, &facts) != 0 || !S_ISREG(facts.st_mode) ||
        (facts.st_mode & (S_IWGRP | S_IWOTH)) != 0) {
        (void)close(descriptor);
        return -1;
    }
    result = add_path_rule(ruleset_fd, descriptor, allowed_access);
    (void)close(descriptor);
    return result;
}

static bool enforce_landlock(bool runtime_v2, int executable_fd, int input_fd,
                             int subject_fd, int toolchain_fd, int output_fd,
                             int scratch_fd) {
    struct ranex_landlock_ruleset_attr ruleset = {0};
    struct stat executable_facts;
    struct stat directory_facts;
    long abi;
    int ruleset_fd;
    __u64 filesystem_mask;
    __u64 executable_access;
    const __u64 readonly_access = LANDLOCK_ACCESS_FS_EXECUTE |
                                  LANDLOCK_ACCESS_FS_READ_FILE |
                                  LANDLOCK_ACCESS_FS_READ_DIR;

    abi = syscall(SYS_landlock_create_ruleset, NULL, 0U,
                  LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < REQUIRED_LANDLOCK_ABI ||
        fstat(executable_fd, &executable_facts) != 0 ||
        (runtime_v2 && fstat(input_fd, &directory_facts) != 0) ||
        (runtime_v2 && !S_ISDIR(directory_facts.st_mode)) ||
        fstat(subject_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        fstat(toolchain_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        fstat(output_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        fstat(scratch_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        !S_ISREG(executable_facts.st_mode)) {
        return false;
    }

    filesystem_mask = landlock_fs_mask(abi);
    ruleset.handled_access_fs = filesystem_mask;
    if (abi >= 4) {
        ruleset.handled_access_net =
            LANDLOCK_ACCESS_NET_BIND_TCP | LANDLOCK_ACCESS_NET_CONNECT_TCP;
    }
    if (abi >= 6) {
        ruleset.scoped = LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET |
                          LANDLOCK_SCOPE_SIGNAL;
    }
    ruleset_fd = (int)syscall(SYS_landlock_create_ruleset, &ruleset,
                              sizeof(ruleset), 0U);
    if (ruleset_fd < 0) {
        return false;
    }

    if (runtime_v2) {
        const __u64 input_access = LANDLOCK_ACCESS_FS_READ_FILE |
                                   LANDLOCK_ACCESS_FS_READ_DIR;
        const __u64 toolchain_access = LANDLOCK_ACCESS_FS_EXECUTE |
                                       LANDLOCK_ACCESS_FS_READ_FILE |
                                       LANDLOCK_ACCESS_FS_READ_DIR;
        executable_access = LANDLOCK_ACCESS_FS_EXECUTE |
                            LANDLOCK_ACCESS_FS_READ_FILE;
        if (add_v2_path_rule(ruleset_fd, executable_fd, executable_access) != 0 ||
            add_v2_path_rule(ruleset_fd, input_fd, input_access) != 0 ||
            add_v2_path_rule(ruleset_fd, subject_fd,
                             v2_subject_allowed_access()) != 0 ||
            add_v2_path_rule(ruleset_fd, toolchain_fd,
                             toolchain_access) != 0 ||
            add_v2_path_rule(ruleset_fd, output_fd, filesystem_mask) != 0 ||
            add_v2_path_rule(ruleset_fd, scratch_fd, filesystem_mask) != 0 ||
            syscall(SYS_landlock_restrict_self, ruleset_fd, 0U) != 0 ||
            close(ruleset_fd) != 0) {
            (void)close(ruleset_fd);
            return false;
        }
        return true;
    }

    /* V1 subject and toolchain remain executable read-only trees.  The two
     * declared writable trees intentionally each receive the complete mask. */
    executable_access = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE;
    if (add_path_rule(ruleset_fd, executable_fd, executable_access) != 0 ||
        /* The pinned x86-64 ELF ABI needs its interpreter and libc before the
         * command can enter its declared toolchain.  Both are exact trusted,
         * read-only runtime objects; no directory or writable host authority
         * is admitted. */
        add_runtime_loader_rule(ruleset_fd, "/lib64/ld-linux-x86-64.so.2",
                                executable_access) != 0 ||
        add_runtime_loader_rule(ruleset_fd, "/lib/x86_64-linux-gnu/libc.so.6",
                                LANDLOCK_ACCESS_FS_READ_FILE) != 0 ||
        add_path_rule(ruleset_fd, subject_fd, readonly_access) != 0 ||
        add_path_rule(ruleset_fd, toolchain_fd, readonly_access) != 0 ||
        add_path_rule(ruleset_fd, output_fd, filesystem_mask) != 0 ||
        add_path_rule(ruleset_fd, scratch_fd, filesystem_mask) != 0 ||
        syscall(SYS_landlock_restrict_self, ruleset_fd, 0U) != 0 ||
        close(ruleset_fd) != 0) {
        (void)close(ruleset_fd);
        return false;
    }
    return true;
}

static bool enforce_v3_landlock(bool verifier_only) {
    struct ranex_landlock_ruleset_attr ruleset = {0};
    long abi = syscall(SYS_landlock_create_ruleset, NULL, 0U,
                       LANDLOCK_CREATE_RULESET_VERSION);
    int ruleset_fd;
    int runtime_fd = -1;
    int input_fd = -1;
    int subject_fd = -1;
    int output_fd = -1;
    int scratch_fd = -1;
    const __u64 read_execute = LANDLOCK_ACCESS_FS_EXECUTE |
                               LANDLOCK_ACCESS_FS_READ_FILE |
                               LANDLOCK_ACCESS_FS_READ_DIR;
    if (abi < REQUIRED_LANDLOCK_ABI) return false;
    ruleset.handled_access_fs = landlock_fs_mask(abi);
    if (abi >= 4) ruleset.handled_access_net = LANDLOCK_ACCESS_NET_BIND_TCP |
                                                LANDLOCK_ACCESS_NET_CONNECT_TCP;
    if (abi >= 6) ruleset.scoped = LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET |
                                   LANDLOCK_SCOPE_SIGNAL;
    ruleset_fd = (int)syscall(SYS_landlock_create_ruleset, &ruleset,
                              sizeof(ruleset), 0U);
    runtime_fd = open("/ranex/runtime", O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (ruleset_fd < 0 || runtime_fd < 0 || add_path_rule(ruleset_fd, runtime_fd, read_execute) != 0)
        goto fail;
    if (!verifier_only) {
        input_fd = open("/ranex/input", O_PATH | O_DIRECTORY | O_CLOEXEC);
        subject_fd = open("/ranex/subject", O_PATH | O_DIRECTORY | O_CLOEXEC);
        output_fd = open("/ranex/output", O_PATH | O_DIRECTORY | O_CLOEXEC);
        scratch_fd = open("/ranex/scratch", O_PATH | O_DIRECTORY | O_CLOEXEC);
        if (input_fd < 0 || subject_fd < 0 || output_fd < 0 || scratch_fd < 0 ||
            add_path_rule(ruleset_fd, input_fd, LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR) != 0 ||
            add_path_rule(ruleset_fd, subject_fd, LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR) != 0 ||
            add_path_rule(ruleset_fd, output_fd, landlock_fs_mask(abi)) != 0 ||
            add_path_rule(ruleset_fd, scratch_fd, landlock_fs_mask(abi)) != 0) goto fail;
    }
    if (syscall(SYS_landlock_restrict_self, ruleset_fd, 0U) != 0) goto fail;
    (void)close(runtime_fd); (void)close(input_fd); (void)close(subject_fd);
    (void)close(output_fd); (void)close(scratch_fd); return close(ruleset_fd) == 0;
fail:
    (void)close(runtime_fd); (void)close(input_fd); (void)close(subject_fd);
    (void)close(output_fd); (void)close(scratch_fd); (void)close(ruleset_fd); return false;
}

/* The profile is x86-64-only: reject a mismatched audit architecture first. */
#define ALLOW_SYSCALL(number)                                                   \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (number), 0, 1),                        \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)

static bool enforce_seccomp(bool runtime_v2) {
    const struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* Minimal static-worker and libc process-startup surface. */
        ALLOW_SYSCALL(__NR_read),
        ALLOW_SYSCALL(__NR_pread64),
        ALLOW_SYSCALL(__NR_write),
        ALLOW_SYSCALL(__NR_dup),
        ALLOW_SYSCALL(__NR_dup2),
        ALLOW_SYSCALL(__NR_dup3),
        ALLOW_SYSCALL(__NR_fcntl),
        ALLOW_SYSCALL(__NR_close),
        ALLOW_SYSCALL(__NR_openat),
        ALLOW_SYSCALL(__NR_newfstatat),
        ALLOW_SYSCALL(__NR_fstat),
        ALLOW_SYSCALL(__NR_lseek),
        ALLOW_SYSCALL(__NR_getdents64),
        ALLOW_SYSCALL(__NR_mmap),
        ALLOW_SYSCALL(__NR_mprotect),
        ALLOW_SYSCALL(__NR_munmap),
        ALLOW_SYSCALL(__NR_brk),
        ALLOW_SYSCALL(__NR_madvise),
        ALLOW_SYSCALL(__NR_rt_sigaction),
        ALLOW_SYSCALL(__NR_rt_sigprocmask),
        ALLOW_SYSCALL(__NR_rt_sigreturn),
        ALLOW_SYSCALL(__NR_arch_prctl),
        ALLOW_SYSCALL(__NR_set_tid_address),
        ALLOW_SYSCALL(__NR_set_robust_list),
        ALLOW_SYSCALL(__NR_rseq),
        ALLOW_SYSCALL(__NR_prlimit64),
        ALLOW_SYSCALL(__NR_clock_gettime),
        ALLOW_SYSCALL(__NR_clock_nanosleep),
        ALLOW_SYSCALL(__NR_getpid),
        ALLOW_SYSCALL(__NR_gettid),
        ALLOW_SYSCALL(__NR_getuid),
        ALLOW_SYSCALL(__NR_getgid),
        ALLOW_SYSCALL(__NR_geteuid),
        ALLOW_SYSCALL(__NR_getegid),
        ALLOW_SYSCALL(__NR_getppid),
        ALLOW_SYSCALL(__NR_getrandom),
        ALLOW_SYSCALL(__NR_futex),
        ALLOW_SYSCALL(__NR_sched_yield),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone, 0, 1),
        BPF_STMT(BPF_RET | BPF_K,
                 seccomp_v3_mode && seccomp_v3_verifier
                     ? SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)
                     : SECCOMP_RET_ALLOW),
        ALLOW_SYSCALL(__NR_execve),
        ALLOW_SYSCALL(__NR_execveat),
        ALLOW_SYSCALL(__NR_wait4),
        ALLOW_SYSCALL(__NR_exit),
        ALLOW_SYSCALL(__NR_exit_group),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_writev, 0, 1),
        BPF_STMT(BPF_RET | BPF_K,
                 seccomp_v3_mode && seccomp_v3_verifier
                     ? SECCOMP_RET_ALLOW
                     : SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_access, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_getcwd, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_ioctl, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_readlink, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_readlinkat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_statx, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_sysinfo, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_unlinkat, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, seccomp_v3_mode ? SECCOMP_RET_ALLOW : SECCOMP_RET_ERRNO | EPERM),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mkdir, 0, 1),
        BPF_STMT(BPF_RET | BPF_K,
                 runtime_v2 ? SECCOMP_RET_ALLOW
                            : SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
    };
    const struct sock_fprog program = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = (struct sock_filter *)filter,
    };
    return syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0U, &program) == 0;
}

static int write_all(int descriptor, const char *buffer, size_t length) {
    while (length != 0U) {
        ssize_t written = write(descriptor, buffer, length);
        if (written < 0 && errno == EINTR) {
            continue;
        }
        if (written <= 0) {
            return -1;
        }
        buffer += (size_t)written;
        length -= (size_t)written;
    }
    return 0;
}

static void v3_diagnostic(const char *reason) {
    char line[256];
    int length = snprintf(line, sizeof(line), "ranex-worker-launcher-v3-error: %s\n",
                          reason == NULL ? "runtime refused" : reason);
    if (length < 0 || (size_t)length >= sizeof(line)) {
        return;
    }
    if (v3_report_descriptor >= 0 && write_all(v3_report_descriptor, line, (size_t)length) == 0) {
        return;
    }
    (void)write_all(STDERR_FILENO, line, (size_t)length);
}

static bool parse_worker_status_fd(const char *argument, int *descriptor) {
    const char *raw;
    char *end = NULL;
    long value;

    if (strncmp(argument, WORKER_STATUS_FD,
                sizeof(WORKER_STATUS_FD) - 1U) != 0) {
        return false;
    }
    raw = argument + sizeof(WORKER_STATUS_FD) - 1U;
    if (*raw == '\0') {
        return false;
    }
    errno = 0;
    value = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        value < WORKER_STATUS_DESCRIPTOR || value > INT_MAX) {
        return false;
    }
    *descriptor = (int)value;
    return true;
}

static bool parse_worker_ready_ack_fd(const char *argument, int *descriptor) {
    const char *raw;
    char *end = NULL;
    long value;

    if (strncmp(argument, WORKER_READY_ACK_FD,
                sizeof(WORKER_READY_ACK_FD) - 1U) != 0) {
        return false;
    }
    raw = argument + sizeof(WORKER_READY_ACK_FD) - 1U;
    if (*raw == '\0') {
        return false;
    }
    errno = 0;
    value = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        value < WORKER_STATUS_DESCRIPTOR || value > INT_MAX) {
        return false;
    }
    *descriptor = (int)value;
    return true;
}

static bool parse_worker_object_fd(const char *argument, const char *prefix,
                                   int *descriptor) {
    const char *raw;
    char *end = NULL;
    long value;
    int held;

    if (*descriptor >= 0 || strncmp(argument, prefix, strlen(prefix)) != 0) {
        return false;
    }
    raw = argument + strlen(prefix);
    if (*raw == '\0') {
        return false;
    }
    errno = 0;
    value = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        value < WORKER_STATUS_DESCRIPTOR || value > INT_MAX) {
        return false;
    }
    held = fcntl((int)value, F_DUPFD_CLOEXEC, WORKER_STATUS_DESCRIPTOR);
    if (held < 0) {
        return false;
    }
    *descriptor = held;
    return true;
}

static int open_worker_executable(const char *path) {
    static const char descriptor_prefix[] = "/proc/self/fd/";
    const char *raw;
    char *end = NULL;
    long descriptor;

    if (strncmp(path, descriptor_prefix, sizeof(descriptor_prefix) - 1U) != 0) {
        return open(path, O_PATH | O_NOFOLLOW | O_CLOEXEC);
    }
    raw = path + sizeof(descriptor_prefix) - 1U;
    if (*raw == '\0') {
        errno = EINVAL;
        return -1;
    }
    errno = 0;
    descriptor = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        descriptor < WORKER_STATUS_DESCRIPTOR || descriptor > INT_MAX) {
        errno = EINVAL;
        return -1;
    }
    return fcntl((int)descriptor, F_DUPFD_CLOEXEC, WORKER_STATUS_DESCRIPTOR);
}

static bool write_namespace_mapping(const char *path, const char *mapping) {
    int descriptor = open(path, O_WRONLY | O_CLOEXEC);
    bool written;

    if (descriptor < 0) {
        return false;
    }
    written = write_all(descriptor, mapping, strlen(mapping)) == 0;
    return close(descriptor) == 0 && written;
}

static bool enter_worker_namespaces(void) {
    const int namespaces = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID |
                           CLONE_NEWIPC | CLONE_NEWNET | CLONE_NEWCGROUP;

    return unshare(namespaces) == 0;
}

static bool enter_worker_namespaces_v2(uid_t *worker_uid, gid_t *worker_gid) {
    const int namespaces = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID |
                           CLONE_NEWIPC | CLONE_NEWNET | CLONE_NEWCGROUP;
    char mapping[64];
    uid_t parent_uid = getuid();
    gid_t parent_gid = getgid();

    if (unshare(namespaces) != 0) {
        return false;
    }
    if (snprintf(mapping, sizeof(mapping), "0 %u 1\n",
                 (unsigned int)parent_uid) < 0 ||
        !write_namespace_mapping("/proc/self/uid_map", mapping) ||
        !write_namespace_mapping("/proc/self/setgroups", "deny\n") ||
        snprintf(mapping, sizeof(mapping), "0 %u 1\n",
                 (unsigned int)parent_gid) < 0 ||
        !write_namespace_mapping("/proc/self/gid_map", mapping)) {
        return false;
    }
    *worker_uid = parent_uid == 0U ? 65534U : parent_uid;
    *worker_gid = parent_gid == 0U ? 65534U : parent_gid;
    return true;
}

static bool enter_unprivileged_worker_user_namespace_v2(uid_t worker_uid,
                                                        gid_t worker_gid) {
    char mapping[64];

    if (unshare(CLONE_NEWUSER) != 0 ||
        snprintf(mapping, sizeof(mapping), "%u 0 1\n",
                 (unsigned int)worker_uid) < 0 ||
        !write_namespace_mapping("/proc/self/uid_map", mapping) ||
        !write_namespace_mapping("/proc/self/setgroups", "deny\n") ||
        snprintf(mapping, sizeof(mapping), "%u 0 1\n",
                 (unsigned int)worker_gid) < 0 ||
        !write_namespace_mapping("/proc/self/gid_map", mapping)) {
        return false;
    }
    return true;
}

static bool drop_worker_capabilities_v2(void) {
    struct ranex_cap_header header = {
        .version = RANEX_LINUX_CAPABILITY_VERSION_3,
        .pid = 0,
    };
    struct ranex_cap_data data[2] = {{0}};

    return syscall(SYS_capset, &header, data) == 0;
}

static bool bind_mount_tree(const char *path, bool readonly) {
    if (mount(path, path, NULL, MS_BIND | MS_REC, NULL) != 0) {
        return false;
    }
    if (readonly && mount(NULL, path, NULL,
                          MS_BIND | MS_REMOUNT | MS_RDONLY | MS_REC, NULL) != 0) {
        return false;
    }
    return true;
}

static bool mount_minimal_dev(void) {
    /* The closed profile declares no device nodes.  An empty tmpfs is therefore
     * the entire /dev authority; adding a host device would be a policy widen. */
    return mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_NOEXEC | MS_NODEV,
                 "mode=755") == 0;
}

static bool same_directory_object(int descriptor, const char *path) {
    struct stat held;
    struct stat named;
    struct stat link;

    return fstat(descriptor, &held) == 0 && S_ISDIR(held.st_mode) &&
           lstat(path, &link) == 0 && !S_ISLNK(link.st_mode) &&
           stat(path, &named) == 0 && S_ISDIR(named.st_mode) &&
           held.st_dev == named.st_dev && held.st_ino == named.st_ino;
}

static int reopen_held_directory_in_mount_namespace(int descriptor) {
    static const char deleted_suffix[] = " (deleted)";
    struct ranex_open_how how = {
        .flags = O_PATH | O_DIRECTORY | O_CLOEXEC,
        .mode = 0U,
        .resolve = RANEX_RESOLVE_BENEATH | RANEX_RESOLVE_NO_SYMLINKS |
                   RANEX_RESOLVE_NO_MAGICLINKS,
    };
    struct stat held;
    struct stat reopened;
    char descriptor_path[64];
    char named_path[PATH_MAX];
    int root_fd = -1;
    int namespace_fd = -1;
    int length;
    ssize_t named_length;

    length = snprintf(descriptor_path, sizeof(descriptor_path),
                      "/proc/self/fd/%d", descriptor);
    if (length < 0 || (size_t)length >= sizeof(descriptor_path) ||
        fstat(descriptor, &held) != 0 || !S_ISDIR(held.st_mode)) {
        return -1;
    }
    named_length = readlink(descriptor_path, named_path, sizeof(named_path) - 1U);
    if (named_length <= 1 || (size_t)named_length >= sizeof(named_path) ||
        named_path[0] != '/') {
        errno = EINVAL;
        return -1;
    }
    named_path[named_length] = '\0';
    if ((size_t)named_length >= sizeof(deleted_suffix) - 1U &&
        memcmp(named_path + named_length - (sizeof(deleted_suffix) - 1U),
               deleted_suffix, sizeof(deleted_suffix) - 1U) == 0) {
        errno = ESTALE;
        return -1;
    }
    root_fd = open("/", O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd < 0) {
        return -1;
    }
    namespace_fd = (int)syscall(
        SYS_openat2, root_fd, named_path + 1, &how, sizeof(how));
    if (namespace_fd < 0 || fstat(namespace_fd, &reopened) != 0 ||
        !S_ISDIR(reopened.st_mode) || held.st_dev != reopened.st_dev ||
        held.st_ino != reopened.st_ino) {
        (void)close(namespace_fd);
        (void)close(root_fd);
        errno = ESTALE;
        return -1;
    }
    if (close(root_fd) != 0) {
        (void)close(namespace_fd);
        return -1;
    }
    return namespace_fd;
}

static int reopen_held_executable_at_virtual_path(int descriptor,
                                                  const char *virtual_path) {
    struct ranex_open_how how = {
        .flags = O_PATH | O_CLOEXEC,
        .mode = 0U,
        .resolve = RANEX_RESOLVE_BENEATH | RANEX_RESOLVE_NO_SYMLINKS |
                   RANEX_RESOLVE_NO_MAGICLINKS,
    };
    struct stat held;
    struct stat reopened;
    int root_fd = -1;
    int namespace_fd = -1;

    if (virtual_path[0] != '/' || virtual_path[1] == '\0' ||
        fstat(descriptor, &held) != 0 || !S_ISREG(held.st_mode)) {
        errno = EINVAL;
        return -1;
    }
    root_fd = open("/", O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (root_fd < 0) {
        return -1;
    }
    namespace_fd = (int)syscall(
        SYS_openat2, root_fd, virtual_path + 1, &how, sizeof(how));
    if (namespace_fd < 0 || fstat(namespace_fd, &reopened) != 0 ||
        !S_ISREG(reopened.st_mode) || held.st_dev != reopened.st_dev ||
        held.st_ino != reopened.st_ino) {
        (void)close(namespace_fd);
        (void)close(root_fd);
        errno = ESTALE;
        return -1;
    }
    if (close(root_fd) != 0) {
        (void)close(namespace_fd);
        return -1;
    }
    return namespace_fd;
}

static bool mount_fresh_proc(void);

static bool assemble_mounts(bool runtime_v2, int input_fd, int subject_fd,
                            int toolchain_fd, int output_fd, int scratch_fd,
                            const char *input, const char *subject,
                            const char *toolchain, const char *output,
                            const char *scratch) {
    bool setup_complete = false;

    (void)input;

    /* New propagation first: no mount operation may escape this namespace.
     * V1 retains its path-preserving bind/remount construction unchanged. */
    if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != 0) {
        return false;
    }
    if (!runtime_v2) {
        setup_complete = bind_mount_tree(subject, true) &&
                         bind_mount_tree(toolchain, true) &&
                         bind_mount_tree(output, false) &&
                         bind_mount_tree(scratch, false);
    } else {
        char root_template[] = "/tmp/ranex-root-XXXXXX";
        char ranex_path[PATH_MAX];
        char old_root_path[PATH_MAX];
        char proc_path[PATH_MAX];
        char dev_path[PATH_MAX];
        char target_paths[5][PATH_MAX];
        const char *target_names[] = {"input", "toolchain", "output", "scratch", "subject"};
        const char *targets[] = {"/ranex/input", "/ranex/toolchain", "/ranex/output",
                                 "/ranex/scratch", "/ranex/subject"};
        int source_fds[] = {input_fd, toolchain_fd, output_fd, scratch_fd, subject_fd};
        int namespace_source_fds[] = {-1, -1, -1, -1, -1};
        int target_fds[] = {-1, -1, -1, -1, -1};
        int mount_fds[] = {-1, -1, -1, -1, -1};
        int root_parent_fd = -1;
        const char *root_name;
        bool root_mounted = false;
        bool pivoted = false;

        if (mkdtemp(root_template) == NULL ||
            snprintf(ranex_path, sizeof(ranex_path), "%s/ranex", root_template) < 0 ||
            snprintf(old_root_path, sizeof(old_root_path), "%s/oldroot", root_template) < 0 ||
            snprintf(proc_path, sizeof(proc_path), "%s/proc", root_template) < 0 ||
            snprintf(dev_path, sizeof(dev_path), "%s/%s", root_template,
                     "dev") < 0) {
            goto v2_cleanup;
        }
        root_name = strrchr(root_template, '/');
        if (root_name == NULL || root_name[1] == '\0') {
            goto v2_cleanup;
        }
        root_name++;
        root_parent_fd = open("/tmp", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
        if (root_parent_fd < 0 ||
            mount("tmpfs", root_template, "tmpfs", MS_NODEV | MS_NOSUID,
                  "mode=755") != 0) {
            goto v2_cleanup;
        }
        root_mounted = true;
        if (mkdir(ranex_path, 0755) != 0 || mkdir(old_root_path, 0755) != 0 ||
            mkdir(proc_path, 0755) != 0 || mkdir(dev_path, 0755) != 0) {
            goto v2_cleanup;
        }
        for (size_t index = 0U; index < 5U; index++) {
            struct stat source_facts;
            int length = snprintf(target_paths[index], sizeof(target_paths[index]),
                                  "%s/%s", ranex_path, target_names[index]);
            if (length < 0 || (size_t)length >= sizeof(target_paths[index]) ||
                mkdir(target_paths[index], 0755) != 0) {
                goto v2_cleanup;
            }
            target_fds[index] = open(target_paths[index], O_PATH | O_DIRECTORY | O_CLOEXEC);
            namespace_source_fds[index] =
                reopen_held_directory_in_mount_namespace(source_fds[index]);
            if (target_fds[index] < 0 || namespace_source_fds[index] < 0 ||
                fstat(source_fds[index], &source_facts) != 0 ||
                !S_ISDIR(source_facts.st_mode)) {
                goto v2_cleanup;
            }
            for (size_t prior = 0U; prior < index; prior++) {
                struct stat current_facts;
                struct stat prior_facts;
                if (fstat(target_fds[index], &current_facts) != 0 ||
                    fstat(target_fds[prior], &prior_facts) != 0 ||
                    (current_facts.st_dev == prior_facts.st_dev &&
                     current_facts.st_ino == prior_facts.st_ino)) {
                    goto v2_cleanup;
                }
            }
        }
        for (size_t index = 0U; index < 5U; index++) {
            struct mount_attr attributes = {0};
            mount_fds[index] = (int)syscall(
                SYS_open_tree, namespace_source_fds[index], "",
                OPEN_TREE_CLONE | OPEN_TREE_CLOEXEC | AT_EMPTY_PATH | AT_RECURSIVE);
            if (mount_fds[index] < 0) {
                goto v2_cleanup;
            }
            if (index == 0U || index == 1U || index == 4U) {
                attributes.attr_set = MOUNT_ATTR_RDONLY;
                if (index == 4U) {
                    attributes.attr_set |= MOUNT_ATTR_NOEXEC;
                }
                if (syscall(SYS_mount_setattr, mount_fds[index], "",
                            AT_EMPTY_PATH | AT_RECURSIVE, &attributes,
                            sizeof(attributes)) != 0) {
                    goto v2_cleanup;
                }
            }
            if (syscall(SYS_move_mount, mount_fds[index], "", target_fds[index], "",
                        MOVE_MOUNT_F_EMPTY_PATH | MOVE_MOUNT_T_EMPTY_PATH) != 0 ||
                close(mount_fds[index]) != 0) {
                mount_fds[index] = -1;
                goto v2_cleanup;
            }
            mount_fds[index] = -1;
            if (!same_directory_object(source_fds[index], target_paths[index])) {
                goto v2_cleanup;
            }
        }
        if (syscall(SYS_pivot_root, root_template, old_root_path) != 0 ||
            chdir("/") != 0) {
            goto v2_cleanup;
        }
        pivoted = true;
        if (!mount_fresh_proc() ||
            unlinkat(root_parent_fd, root_name, AT_REMOVEDIR) != 0 ||
            umount2("/oldroot", MNT_DETACH) != 0 || rmdir("/oldroot") != 0) {
            goto v2_cleanup;
        }
        for (size_t index = 0U; index < 5U; index++) {
            if (!same_directory_object(source_fds[index], targets[index])) {
                goto v2_cleanup;
            }
        }
        setup_complete = true;

v2_cleanup:
        for (size_t index = 0U; index < 5U; index++) {
            if (mount_fds[index] >= 0) {
                (void)close(mount_fds[index]);
            }
            if (target_fds[index] >= 0) {
                (void)close(target_fds[index]);
            }
            if (namespace_source_fds[index] >= 0) {
                (void)close(namespace_source_fds[index]);
            }
        }
        if (!pivoted && root_mounted) {
            (void)umount2(root_template, MNT_DETACH);
        }
        if (!pivoted) {
            (void)rmdir(root_template);
        }
        if (root_parent_fd >= 0) {
            (void)close(root_parent_fd);
        }
    }
    return setup_complete && mount_minimal_dev();
}

static bool assemble_mounts_v2(int input_fd, int subject_fd, int toolchain_fd,
                               int output_fd, int scratch_fd) {
    return assemble_mounts(true, input_fd, subject_fd, toolchain_fd, output_fd,
                           scratch_fd, NULL, NULL, NULL, NULL, NULL);
}

static bool mount_fresh_proc(void) {
    /* CLONE_NEWPID takes effect only after fork.  Overlay proc in that child so
     * process views name the final PID namespace, never the launcher parent. */
    return mount("proc", "/proc", "proc", MS_NOSUID | MS_NOEXEC | MS_NODEV,
                 NULL) == 0;
}

static int wait_for_worker(int child) {
    int status;

    for (;;) {
        if (waitpid(child, &status, 0) >= 0) {
            break;
        }
        if (errno != EINTR) {
            return 64;
        }
    }
    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }
    if (WIFSIGNALED(status)) {
        return 128 + WTERMSIG(status);
    }
    return 64;
}

static bool close_worker_descriptors(int status_descriptor, int acknowledgement_descriptor,
                                     int verifier_ack_descriptor,
                                     int diagnostic_descriptor) {
    int preserved[] = {status_descriptor, acknowledgement_descriptor,
                       verifier_ack_descriptor, diagnostic_descriptor};
    size_t preserved_count = 0U;
    unsigned int cursor = 4U;
    long maximum;

    for (size_t index = 0U; index < sizeof(preserved) / sizeof(preserved[0]); index++) {
        if (preserved[index] < 4) continue;
        bool duplicate = false;
        for (size_t prior = 0U; prior < preserved_count; prior++)
            if (preserved[prior] == preserved[index]) duplicate = true;
        if (!duplicate) preserved[preserved_count++] = preserved[index];
    }
    qsort(preserved, preserved_count, sizeof(preserved[0]), compare_ints);
    for (size_t index = 0U; index < preserved_count; index++) {
        unsigned int keep = (unsigned int)preserved[index];
        if (cursor < keep && syscall(SYS_close_range, cursor, keep - 1U, 0U) != 0 &&
            errno != ENOSYS) return false;
        cursor = keep + 1U;
    }
    if (syscall(SYS_close_range, cursor, UINT_MAX, 0U) == 0) return true;
    if (errno != ENOSYS) return false;

    maximum = sysconf(_SC_OPEN_MAX);
    if (maximum < 0) {
        maximum = 65536;
    }
    for (int descriptor = 4; descriptor < maximum; descriptor++) {
        if (descriptor != status_descriptor && descriptor != acknowledgement_descriptor &&
            descriptor != verifier_ack_descriptor && descriptor != diagnostic_descriptor) {
            (void)close(descriptor);
        }
    }
    return true;
}

static void close_all_descriptors(void) {
    long maximum;

    errno = 0;
    if (syscall(SYS_close_range, 0U, UINT_MAX, 0U) == 0 || errno != ENOSYS) {
        return;
    }
    maximum = sysconf(_SC_OPEN_MAX);
    if (maximum < 0) {
        maximum = 65536;
    }
    for (int descriptor = 0; descriptor < maximum; descriptor++) {
        (void)close(descriptor);
    }
}

static int protocol_refusal(void) {
    static const char response[] =
        "{\"probes\":{},\"protocol\":\"ranex-launcher-v1\","
        "\"refusal\":\"E-C17-PROTOCOL\"}";
    (void)write_all(5, response, sizeof(response) - 1U);
    return 64;
}

static int host_fact_refusal(void) {
    static const char response[] =
        "{\"probes\":{},\"protocol\":\"ranex-launcher-v1\","
        "\"refusal\":\"E-C17-HOST-FACT-MISSING\"}";
    (void)write_all(5, response, sizeof(response) - 1U);
    return 65;
}

static bool fixed_descriptor(int descriptor, int access_mode) {
    struct stat facts;
    int flags;
    if (fstat(descriptor, &facts) != 0 || !S_ISFIFO(facts.st_mode)) {
        return false;
    }
    flags = fcntl(descriptor, F_GETFL);
    return flags >= 0 && (flags & O_ACCMODE) == access_mode;
}

static int compare_ints(const void *left, const void *right) {
    int first = *(const int *)left;
    int second = *(const int *)right;
    return (first > second) - (first < second);
}

static bool ascii_digit(char value) {
    return value >= '0' && value <= '9';
}

static size_t enumerate_unexpected_fds(int *found, size_t capacity) {
    DIR *directory = opendir("/proc/self/fd");
    struct dirent *entry;
    size_t count = 0U;
    int directory_fd;
    if (directory == NULL) {
        return SIZE_MAX;
    }
    directory_fd = dirfd(directory);
    errno = 0;
    while ((entry = readdir(directory)) != NULL) {
        char *end = NULL;
        long value;
        errno = 0;
        value = strtol(entry->d_name, &end, 10);
        if (errno != 0 || end == entry->d_name || *end != '\0') {
            continue;
        }
        if ((value < 3 || value > 5) && value != directory_fd) {
            if (count >= capacity || value > INT_MAX) {
                (void)closedir(directory);
                return SIZE_MAX;
            }
            found[count++] = (int)value;
        }
    }
    if (errno != 0 || closedir(directory) != 0) {
        return SIZE_MAX;
    }
    qsort(found, count, sizeof(found[0]), compare_ints);
    return count;
}

static bool consume_literal(char **cursor, const char *end, const char *literal) {
    size_t length = strlen(literal);
    if ((size_t)(end - *cursor) < length || memcmp(*cursor, literal, length) != 0) {
        return false;
    }
    *cursor += length;
    return true;
}

static bool parse_json_string(char **cursor, const char *end, char *output,
                              size_t capacity) {
    size_t used = 0U;
    if (*cursor == end || *(*cursor)++ != '"') {
        return false;
    }
    while (*cursor != end && **cursor != '"') {
        unsigned char value = (unsigned char)**cursor;
        if (value < 0x20U || value == '\\' || used + 1U >= capacity) {
            return false;
        }
        output[used++] = (char)value;
        (*cursor)++;
    }
    if (*cursor == end || *(*cursor)++ != '"') {
        return false;
    }
    output[used] = '\0';
    return true;
}

static bool valid_environment_name(const char *name) {
    if ((*name < 'A' || *name > 'Z') && (*name < 'a' || *name > 'z') &&
        *name != '_') {
        return false;
    }
    for (name++; *name != '\0'; name++) {
        if ((*name < 'A' || *name > 'Z') && (*name < 'a' || *name > 'z') &&
            !ascii_digit(*name) && *name != '_') {
            return false;
        }
    }
    return true;
}

static bool parse_allowlist(char **cursor, const char *end,
                            struct probe_request *request) {
    bool lc_all = false;
    bool timezone = false;
    if (*cursor == end || *(*cursor)++ != '[') {
        return false;
    }
    for (;;) {
        char *name;
        if (request->environment_count >= ENVIRONMENT_LIMIT) {
            return false;
        }
        name = request->environment_names[request->environment_count];
        if (!parse_json_string(cursor, end, name, ENVIRONMENT_NAME_LIMIT) ||
            !valid_environment_name(name)) {
            return false;
        }
        for (size_t index = 0U; index < request->environment_count; index++) {
            if (strcmp(request->environment_names[index], name) == 0) {
                return false;
            }
        }
        request->environment_count++;
        if (strcmp(name, "LC_ALL") == 0) {
            lc_all = true;
        } else if (strcmp(name, "TZ") == 0) {
            timezone = true;
        }
        if (*cursor == end) {
            return false;
        }
        if (**cursor == ']') {
            (*cursor)++;
            return lc_all && timezone;
        }
        if (*(*cursor)++ != ',') {
            return false;
        }
    }
}

static bool parse_nonnegative_long(char **cursor, const char *end, long *value) {
    char *number_end;
    if (*cursor == end || !ascii_digit(**cursor)) {
        return false;
    }
    errno = 0;
    *value = strtol(*cursor, &number_end, 10);
    if (errno != 0 || number_end > end || *value < 0) {
        return false;
    }
    *cursor = number_end;
    return true;
}

static bool parse_expected_closed(char **cursor, const char *end,
                                  struct stage_metadata *metadata) {
    int previous = -1;
    if (*cursor == end || *(*cursor)++ != '[') {
        return false;
    }
    while (*cursor != end && **cursor != ']') {
        long value;
        if (metadata->closed_count >= CLOSED_FD_LIMIT ||
            !parse_nonnegative_long(cursor, end, &value) || value > INT_MAX ||
            value <= previous) {
            return false;
        }
        metadata->closed[metadata->closed_count++] = (int)value;
        previous = (int)value;
        if (*cursor == end || (**cursor != ',' && **cursor != ']')) {
            return false;
        }
        if (**cursor == ',') {
            (*cursor)++;
        }
    }
    if (*cursor == end || *(*cursor)++ != ']') {
        return false;
    }
    return metadata->closed_count >= 3U && metadata->closed[0] == 0 &&
           metadata->closed[1] == 1 && metadata->closed[2] == 2;
}

static int read_request(struct probe_request *request) {
    char buffer[REQUEST_LIMIT + 1U];
    char *cursor;
    const char *end;
    size_t used = 0U;
    memset(request, 0, sizeof(*request));
    for (;;) {
        ssize_t received = read(4, buffer + used, sizeof(buffer) - used);
        if (received < 0 && errno == EINTR) {
            continue;
        }
        if (received < 0) {
            return -1;
        }
        if (received == 0) {
            break;
        }
        used += (size_t)received;
        if (used > REQUEST_LIMIT) {
            return -1;
        }
    }
    cursor = buffer;
    end = buffer + used;
    if (!consume_literal(&cursor, end,
                         "{\"action\":\"qualify-probe\",\"env_allowlist\":") ||
        !parse_allowlist(&cursor, end, request) ||
        !consume_literal(&cursor, end,
                         ",\"protocol\":\"ranex-launcher-v1\"}") ||
        cursor != end) {
        return -1;
    }
    return 0;
}

static long session_keyring_id(void) {
    return syscall(SYS_keyctl, KEYCTL_GET_KEYRING_ID, KEY_SPEC_SESSION_KEYRING, 0);
}

static int append_number(char *buffer, size_t capacity, size_t *used, long value) {
    int length;
    if (*used >= capacity) {
        return -1;
    }
    length = snprintf(buffer + *used, capacity - *used, "%ld", value);
    if (length < 0 || (size_t)length >= capacity - *used) {
        return -1;
    }
    *used += (size_t)length;
    return 0;
}

static char **build_environment(const struct probe_request *request) {
    char **environment = calloc(request->environment_count + 1U, sizeof(char *));
    size_t used = 0U;
    if (environment == NULL) {
        return NULL;
    }
    for (size_t index = 0U; index < request->environment_count; index++) {
        const char *name = request->environment_names[index];
        const char *value = getenv(name);
        size_t name_length;
        size_t value_length;
        size_t entry_length;
        if (value == NULL) {
            continue;
        }
        name_length = strlen(name);
        value_length = strlen(value);
        if (name_length > SIZE_MAX - value_length - 2U) {
            return NULL;
        }
        entry_length = name_length + value_length + 2U;
        environment[used] = malloc(entry_length);
        if (environment[used] == NULL ||
            snprintf(environment[used], entry_length, "%s=%s", name, value) < 0) {
            return NULL;
        }
        used++;
    }
    environment[used] = NULL;
    return environment;
}

static bool install_stage_metadata(long session_keyring_before,
                                   const char *closed_json) {
    int descriptors[2];
    char payload[REQUEST_LIMIT + 1U];
    int length = snprintf(payload, sizeof(payload), "%ld:%s", session_keyring_before,
                          closed_json);
    if (length < 0 || (size_t)length >= sizeof(payload) ||
        pipe2(descriptors, O_CLOEXEC) != 0) {
        return false;
    }
    if (write_all(descriptors[1], payload, (size_t)length) != 0 ||
        close(descriptors[1]) != 0) {
        (void)close(descriptors[0]);
        return false;
    }
    if (dup2(descriptors[0], 4) != 4) {
        (void)close(descriptors[0]);
        return false;
    }
    if (descriptors[0] != 4 && close(descriptors[0]) != 0) {
        return false;
    }
    return true;
}

static int stage_one(void) {
    struct probe_request request;
    int unexpected[CLOSED_FD_LIMIT];
    size_t unexpected_count;
    long before;
    long after;
    char *arguments[3];
    char **environment;
    char closed_argument[8192];
    size_t closed_used = 0U;

    if (!fixed_descriptor(3, O_RDONLY) || !fixed_descriptor(4, O_RDONLY) ||
        !fixed_descriptor(5, O_WRONLY)) {
        return 64;
    }
    if (read_request(&request) != 0) {
        return protocol_refusal();
    }

    unexpected_count =
        enumerate_unexpected_fds(unexpected, CLOSED_FD_LIMIT - 3U);
    if (unexpected_count == SIZE_MAX) {
        return 64;
    }
    memcpy(closed_argument, "[0,1,2", sizeof("[0,1,2") - 1U);
    closed_used = sizeof("[0,1,2") - 1U;
    for (size_t index = 0U; index < unexpected_count; index++) {
        if (unexpected[index] <= 2) {
            continue;
        }
        closed_argument[closed_used++] = ',';
        if (append_number(closed_argument, sizeof(closed_argument), &closed_used,
                          unexpected[index]) != 0) {
            return 64;
        }
    }
    if (closed_used + 2U > sizeof(closed_argument)) {
        return 64;
    }
    closed_argument[closed_used++] = ']';
    closed_argument[closed_used] = '\0';

    environment = build_environment(&request);
    if (environment == NULL) {
        return 64;
    }
    (void)close(0);
    (void)close(1);
    (void)close(2);
    errno = 0;
    int close_result = (int)syscall(SYS_close_range, 6U, UINT_MAX, 0U);
    int close_error = errno;
    if (close_result != 0 && close_error != ENOSYS) {
        return 64;
    }
    if (close_result != 0) {
        long maximum = sysconf(_SC_OPEN_MAX);
        if (maximum < 0) {
            maximum = 65536;
        }
        for (int descriptor = 6; descriptor < maximum; descriptor++) {
            (void)close(descriptor);
        }
    }

    before = session_keyring_id();
    after = syscall(SYS_keyctl, KEYCTL_JOIN_SESSION_KEYRING, 0);
    if (before < 0 || after < 0 || after == before) {
        return 64;
    }

    if (!install_stage_metadata(before, closed_argument)) {
        return 64;
    }
    arguments[0] = (char *)"ranex-worker-launcher";
    arguments[1] = (char *)STAGE_TWO;
    arguments[2] = NULL;
    execve("/proc/self/exe", arguments, environment);
    return 64;
}

static int compare_names(const void *left, const void *right) {
    return strcmp((const char *)left, (const char *)right);
}

static bool observe_environment(char *names_json, size_t names_capacity) {
    char observed[8192];
    char names[ENVIRONMENT_LIMIT][ENVIRONMENT_NAME_LIMIT];
    size_t used = 0U;
    size_t names_used = 0U;
    size_t name_count = 0U;
    int descriptor;
    descriptor = open("/proc/self/environ", O_RDONLY | O_CLOEXEC);
    if (descriptor < 0) {
        return false;
    }
    for (;;) {
        ssize_t count = read(descriptor, observed + used, sizeof(observed) - used);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count < 0) {
            (void)close(descriptor);
            return false;
        }
        if (count == 0) {
            break;
        }
        used += (size_t)count;
        if (used == sizeof(observed)) {
            (void)close(descriptor);
            return false;
        }
    }
    if (close(descriptor) != 0) {
        return false;
    }
    for (size_t offset = 0U; offset < used;) {
        char *assignment = observed + offset;
        size_t assignment_length = strnlen(assignment, used - offset);
        char *separator;
        size_t name_length;
        if (assignment_length == used - offset || name_count >= ENVIRONMENT_LIMIT) {
            return false;
        }
        separator = memchr(assignment, '=', assignment_length);
        if (separator == NULL) {
            return false;
        }
        name_length = (size_t)(separator - assignment);
        if (name_length == 0U || name_length >= ENVIRONMENT_NAME_LIMIT) {
            return false;
        }
        memcpy(names[name_count], assignment, name_length);
        names[name_count][name_length] = '\0';
        if (!valid_environment_name(names[name_count])) {
            return false;
        }
        name_count++;
        offset += assignment_length + 1U;
    }
    qsort(names, name_count, sizeof(names[0]), compare_names);
    if (names_capacity < 3U) {
        return false;
    }
    names_json[names_used++] = '[';
    for (size_t index = 0U; index < name_count; index++) {
        size_t name_length = strlen(names[index]);
        size_t required = name_length + (index == 0U ? 2U : 3U);
        if (required >= names_capacity - names_used) {
            return false;
        }
        if (index != 0U) {
            names_json[names_used++] = ',';
        }
        names_json[names_used++] = '"';
        memcpy(names_json + names_used, names[index], name_length);
        names_used += name_length;
        names_json[names_used++] = '"';
    }
    names_json[names_used++] = ']';
    names_json[names_used] = '\0';
    return true;
}

static bool status_facts(int *no_new_privs) {
    char buffer[8192];
    ssize_t count;
    int descriptor = open("/proc/self/status", O_RDONLY | O_CLOEXEC);
    char *nnp;
    if (descriptor < 0) {
        return false;
    }
    count = read(descriptor, buffer, sizeof(buffer) - 1U);
    (void)close(descriptor);
    if (count <= 0 || (size_t)count == sizeof(buffer) - 1U) {
        return false;
    }
    buffer[count] = '\0';
    if (strstr(buffer, "Seccomp:") == NULL || strstr(buffer, "Seccomp_filters:") == NULL) {
        return false;
    }
    nnp = strstr(buffer, "NoNewPrivs:");
    if (nnp == NULL || sscanf(nnp, "NoNewPrivs:\t%d", no_new_privs) != 1) {
        return false;
    }
    return true;
}

static bool descriptor_absent(int descriptor) {
    errno = 0;
    return fcntl(descriptor, F_GETFD) == -1 && errno == EBADF;
}

static bool read_stage_metadata(struct stage_metadata *metadata) {
    char buffer[REQUEST_LIMIT + 1U];
    char *cursor;
    const char *end;
    size_t used = 0U;
    memset(metadata, 0, sizeof(*metadata));
    for (;;) {
        ssize_t received = read(4, buffer + used, sizeof(buffer) - used);
        if (received < 0 && errno == EINTR) {
            continue;
        }
        if (received < 0) {
            return false;
        }
        if (received == 0) {
            break;
        }
        used += (size_t)received;
        if (used > REQUEST_LIMIT) {
            return false;
        }
    }
    buffer[used] = '\0';
    cursor = buffer;
    end = buffer + used;
    if (!parse_nonnegative_long(&cursor, end, &metadata->session_keyring_before) ||
        metadata->session_keyring_before <= 0 || !consume_literal(&cursor, end, ":")) {
        return false;
    }
    return parse_expected_closed(&cursor, end, metadata) && cursor == end;
}

static int stage_two(int argc, char **argv) {
    struct stage_metadata metadata;
    int unexpected[CLOSED_FD_LIMIT];
    size_t unexpected_count;
    char gate;
    char response[RESPONSE_LIMIT];
    char closed_json[8192];
    char observed_names_json[8192];
    size_t closed_used = 0U;
    long after;
    int no_new_privs = 0;
    long landlock_abi;
    int length;
    bool exact_fd_set;
    bool secret_absent;

    if (argc != 2 || strcmp(argv[1], STAGE_TWO) != 0 ||
        !fixed_descriptor(3, O_RDONLY) || !fixed_descriptor(4, O_RDONLY) ||
        !fixed_descriptor(5, O_WRONLY)) {
        return protocol_refusal();
    }
    if (!read_stage_metadata(&metadata)) {
        return protocol_refusal();
    }
    unexpected_count = enumerate_unexpected_fds(unexpected, CLOSED_FD_LIMIT);
    exact_fd_set = unexpected_count == 0U;
    if (unexpected_count == SIZE_MAX || !exact_fd_set) {
        return 64;
    }
    after = session_keyring_id();
    if (after <= 0 ||
        !observe_environment(observed_names_json, sizeof(observed_names_json)) ||
        prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        return 64;
    }
    secret_absent = getenv(INJECTED_SECRET_NAME) == NULL;

    closed_json[closed_used++] = '[';
    for (size_t index = 0U; index < metadata.closed_count; index++) {
        int descriptor = metadata.closed[index];
        if (!descriptor_absent(descriptor)) {
            return host_fact_refusal();
        }
        if (index != 0U) {
            closed_json[closed_used++] = ',';
        }
        if (append_number(closed_json, sizeof(closed_json), &closed_used, descriptor) != 0) {
            return protocol_refusal();
        }
    }
    if (closed_used + 2U > sizeof(closed_json)) {
        return protocol_refusal();
    }
    closed_json[closed_used++] = ']';
    closed_json[closed_used] = '\0';

    if (after == metadata.session_keyring_before) {
        return host_fact_refusal();
    }
    for (;;) {
        ssize_t received = read(3, &gate, 1U);
        if (received < 0 && errno == EINTR) {
            continue;
        }
        if (received != 1) {
            return protocol_refusal();
        }
        break;
    }

    landlock_abi = syscall(SYS_landlock_create_ruleset, NULL, 0U,
                           LANDLOCK_CREATE_RULESET_VERSION);
    if (landlock_abi < REQUIRED_LANDLOCK_ABI || !exact_fd_set ||
        session_keyring_id() != after || !status_facts(&no_new_privs) ||
        no_new_privs != 1) {
        return host_fact_refusal();
    }

    length = snprintf(
        response, sizeof(response),
        "{\"probes\":{\"closed_unexpected_fds\":%s,"
        "\"inherited_session_keyring_invalidated\":true,"
        "\"injected_secret_env_absent\":%s,"
        "\"injected_unexpected_fd_absent\":%s,\"landlock_abi\":%ld,"
        "\"no_new_privs\":1,\"observed_env_names\":%s,"
        "\"seccomp_fields_present\":true,\"session_keyring_after\":%ld,"
        "\"session_keyring_before\":%ld},\"protocol\":"
        "\"ranex-launcher-v1\",\"refusal\":null}",
        closed_json, secret_absent ? "true" : "false",
        exact_fd_set ? "true" : "false", landlock_abi, observed_names_json, after,
        metadata.session_keyring_before);
    if (length < 0 || (size_t)length >= sizeof(response)) {
        return protocol_refusal();
    }
    if (write_all(5, response, (size_t)length) != 0) {
        return 66;
    }
    return 0;
}

/*
 * Execute a single already-resolved worker beneath its sole writable directory.
 * This is deliberately a separate, closed invocation from the qualification
 * protocol: qualification never accepts a command payload.
 */
static int worker_exec(int argc, char **argv) {
    struct probe_request worker_environment_request = {
        .environment_names = {"LC_ALL", "TZ"},
        .environment_count = 2U,
    };
    bool runtime_v2 = false;
    bool runtime_v3 = false;
    int input_fd = -1;
    int subject_fd = -1;
    int toolchain_fd = -1;
    int output_fd = -1;
    int scratch_fd = -1;
    int executable_fd = -1;
    int status_descriptor = -1;
    int acknowledgement_descriptor = -1;
    struct v3_runtime_map v3_map = {.map_fd = -1, .report_fd = -1, .ack_fd = -1,
                                    .readback_fd = -1,
                                    .loader_fd = -1, .input_fd = -1, .subject_fd = -1,
                                    .output_fd = -1, .scratch_fd = -1,
                                    .verifier_procs_fd = -1, .verifier_events_fd = -1,
                                    .verifier_kill_fd = -1};
    int argument_offset = 2;
    int subject_index = -1;
    int toolchain_index = -1;
    int output_index = -1;
    int scratch_index = -1;
    int executable_index = -1;
    uid_t worker_uid = 0U;
    gid_t worker_gid = 0U;
    int pid_pipe[2];
    pid_t worker;
    long controller_visible_pid;
    char **environment;
    char readiness[256];
    int readiness_length;
    char *v3_argv[REQUEST_LIMIT / 2U];

    while (argc > argument_offset && strncmp(argv[argument_offset], "--ranex-", 8U) == 0) {
        if (strncmp(argv[argument_offset], WORKER_STATUS_FD,
                    sizeof(WORKER_STATUS_FD) - 1U) == 0) {
            if (status_descriptor >= 0 ||
                !parse_worker_status_fd(argv[argument_offset], &status_descriptor)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_READY_ACK_FD,
                           sizeof(WORKER_READY_ACK_FD) - 1U) == 0) {
            if (acknowledgement_descriptor >= 0 ||
                !parse_worker_ready_ack_fd(argv[argument_offset], &acknowledgement_descriptor)) {
                return 64;
            }
        } else if (strcmp(argv[argument_offset], WORKER_RUNTIME_V2) == 0) {
            if (runtime_v2) {
                return 64;
            }
            runtime_v2 = true;
        } else if (strcmp(argv[argument_offset], WORKER_RUNTIME_V3) == 0) {
            if (runtime_v2 || runtime_v3) {
                return 64;
            }
            runtime_v3 = true;
        } else if (strncmp(argv[argument_offset], WORKER_RUNTIME_V3_PREFIX,
                           sizeof(WORKER_RUNTIME_V3_PREFIX) - 1U) == 0) {
            if (runtime_v2 || runtime_v3 ||
                !parse_v3_bundle(argv[argument_offset] + sizeof(WORKER_RUNTIME_V3_PREFIX) - 1U,
                                 &v3_map)) return 64;
            runtime_v3 = true;
        } else if (strncmp(argv[argument_offset], WORKER_INPUT_FD,
                           sizeof(WORKER_INPUT_FD) - 1U) == 0) {
            if (!runtime_v2 ||
                !parse_worker_object_fd(argv[argument_offset], WORKER_INPUT_FD,
                                        &input_fd)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_SUBJECT_FD,
                           sizeof(WORKER_SUBJECT_FD) - 1U) == 0) {
            if (!runtime_v2 ||
                !parse_worker_object_fd(argv[argument_offset], WORKER_SUBJECT_FD,
                                        &subject_fd)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_TOOLCHAIN_FD,
                           sizeof(WORKER_TOOLCHAIN_FD) - 1U) == 0) {
            if (!runtime_v2 ||
                !parse_worker_object_fd(argv[argument_offset], WORKER_TOOLCHAIN_FD,
                                        &toolchain_fd)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_OUTPUT_FD,
                           sizeof(WORKER_OUTPUT_FD) - 1U) == 0) {
            if (!runtime_v2 ||
                !parse_worker_object_fd(argv[argument_offset], WORKER_OUTPUT_FD,
                                        &output_fd)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_SCRATCH_FD,
                           sizeof(WORKER_SCRATCH_FD) - 1U) == 0) {
            if (!runtime_v2 ||
                !parse_worker_object_fd(argv[argument_offset], WORKER_SCRATCH_FD,
                                        &scratch_fd)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_EXECUTABLE_FD,
                           sizeof(WORKER_EXECUTABLE_FD) - 1U) == 0) {
            if (!runtime_v2 ||
                !parse_worker_object_fd(argv[argument_offset], WORKER_EXECUTABLE_FD,
                                        &executable_fd)) {
                return 64;
            }
        } else {
            return 64;
        }
        argument_offset++;
    }
    if (status_descriptor >= 0 &&
        (acknowledgement_descriptor < 0 || acknowledgement_descriptor == status_descriptor)) {
        return 64;
    }
    if (runtime_v3) {
        if (v3_map.map_fd < 0 || v3_map.report_fd < 0 || v3_map.ack_fd < 0 ||
            v3_map.readback_fd < 0 || v3_map.verifier_procs_fd < 0 ||
            v3_map.verifier_events_fd < 0 || v3_map.verifier_kill_fd < 0 ||
            argc <= argument_offset || argv[argument_offset][0] != '/') return 64;
        if (!read_v3_map(&v3_map)) return 64;
        executable_fd = fcntl(v3_map.loader_fd, F_DUPFD_CLOEXEC, WORKER_STATUS_DESCRIPTOR);
        if (executable_fd < 0) return 64;
        subject_index = argument_offset + 1;
        output_index = argument_offset + 2;
        scratch_index = argument_offset + 3;
        executable_index = argument_offset + 4;
        if (argc < executable_index + 1 || argv[executable_index][0] != '/') return 64;
    } else if (runtime_v2) {
        executable_index = argument_offset;
        if (argc < executable_index + 1 ||
            strncmp(argv[executable_index], "/ranex/toolchain/",
                    sizeof("/ranex/toolchain/") - 1U) != 0 ||
            argv[executable_index][sizeof("/ranex/toolchain/") - 1U] == '\0' ||
            input_fd < 0 || subject_fd < 0 || toolchain_fd < 0 || output_fd < 0 ||
            scratch_fd < 0 || executable_fd < 0) {
            return 64;
        }
    } else {
        subject_index = argument_offset;
        toolchain_index = subject_index + 1;
        output_index = subject_index + 2;
        scratch_index = subject_index + 3;
        executable_index = subject_index + 4;
        if (argc < executable_index + 1 || argv[subject_index][0] != '/' ||
            argv[toolchain_index][0] != '/' || argv[output_index][0] != '/' ||
            argv[scratch_index][0] != '/' || argv[executable_index][0] != '/') {
            return 64;
        }
    }
    if ((runtime_v2 || runtime_v3) && !enter_worker_namespaces_v2(&worker_uid, &worker_gid)) {
        return 64;
    }
    if (!runtime_v2 && !runtime_v3) {
        subject_fd = open(argv[subject_index], O_PATH | O_DIRECTORY | O_CLOEXEC);
        toolchain_fd = open(argv[toolchain_index], O_PATH | O_DIRECTORY | O_CLOEXEC);
        output_fd = open(argv[output_index], O_PATH | O_DIRECTORY | O_CLOEXEC);
        scratch_fd = open(argv[scratch_index], O_PATH | O_DIRECTORY | O_CLOEXEC);
        executable_fd = open_worker_executable(argv[executable_index]);
    }
    if ((runtime_v2 && input_fd < 0) || (runtime_v3 &&
         (v3_map.map_fd < 0 || v3_map.input_fd < 0 || v3_map.subject_fd < 0 ||
          v3_map.output_fd < 0 || v3_map.scratch_fd < 0)) ||
        (!runtime_v3 && (subject_fd < 0 || output_fd < 0 || scratch_fd < 0)) ||
        (!runtime_v3 && toolchain_fd < 0) ||
        executable_fd < 0) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    environment = build_environment(&worker_environment_request);
    if (environment == NULL) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    /* CLONE_NEWPID takes effect in this forked child; the outer launcher only
     * waits and relays its exit status, so the command itself owns every
     * namespace named in the readiness record.  Mount propagation and all
     * descriptor-tree mounts happen before the fork; proc must wait until it. */
    if (!runtime_v2 && !runtime_v3 && !enter_worker_namespaces()) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (!runtime_v2 && !runtime_v3 &&
        !assemble_mounts(false, input_fd, subject_fd, toolchain_fd,
                         output_fd, scratch_fd, NULL, argv[subject_index],
                         argv[toolchain_index], argv[output_index],
                         argv[scratch_index])) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (pipe2(pid_pipe, O_CLOEXEC) != 0) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    worker = fork();
    if (worker < 0) {
        (void)close(pid_pipe[0]);
        (void)close(pid_pipe[1]);
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (worker > 0) {
        controller_visible_pid = (long)worker;
        (void)close(pid_pipe[0]);
        if (write_all(pid_pipe[1], (const char *)&controller_visible_pid,
                      sizeof(controller_visible_pid)) != 0) {
            (void)close(pid_pipe[1]);
            return 64;
        }
        (void)close(pid_pipe[1]);
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        if (status_descriptor >= 0) {
            (void)close(status_descriptor);
        }
        close_all_descriptors();
        return wait_for_worker(worker);
    }
    (void)close(pid_pipe[1]);
    if (read(pid_pipe[0], &controller_visible_pid,
             sizeof(controller_visible_pid)) != (ssize_t)sizeof(controller_visible_pid) ||
        close(pid_pipe[0]) != 0 || controller_visible_pid <= 0) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (runtime_v2) {
        int namespace_executable = -1;

        if (!assemble_mounts_v2(input_fd, subject_fd, toolchain_fd, output_fd,
                                scratch_fd)) {
            return 64;
        }
        namespace_executable = reopen_held_executable_at_virtual_path(
            executable_fd, argv[executable_index]);
        if (namespace_executable < 0 || close(executable_fd) != 0) {
            (void)close(namespace_executable);
            return 64;
        }
        executable_fd = namespace_executable;
        if (!enter_unprivileged_worker_user_namespace_v2(worker_uid, worker_gid)) {
            return 64;
        }
    } else if (runtime_v3) {
        if (assemble_v3_runtime(&v3_map, "/") != 0 ||
            write_v3_readbacks(&v3_map) != 0 ||
            run_v3_verifier("/", &v3_map) != 0) return 64;
    }
    if ((!runtime_v2 && !runtime_v3 && !mount_fresh_proc()) ||
        (runtime_v2 ? chdir("/ranex/input") : runtime_v3 ? chdir("/") : fchdir(scratch_fd)) != 0 ||
        ((runtime_v2 || runtime_v3) && !drop_worker_capabilities_v2()) ||
        prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 ||
        (!runtime_v3 && !enforce_landlock(runtime_v2, executable_fd, input_fd, subject_fd,
                                          toolchain_fd, output_fd, scratch_fd))) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }

    /* Keep the executable on a fixed descriptor, then remove every inherited
     * authority.  This is stage one's close discipline with its protocol FDs
     * replaced by the sole object needed by execveat. */
    if (executable_fd != 3 && dup2(executable_fd, 3) != 3) {
        (void)close(input_fd);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (!runtime_v3 && ((input_fd >= 0 && input_fd != 3 && close(input_fd) != 0) ||
        (subject_fd != 3 && close(subject_fd) != 0) ||
        (toolchain_fd != 3 && close(toolchain_fd) != 0) ||
        (output_fd != 3 && close(output_fd) != 0) ||
        (scratch_fd != 3 && close(scratch_fd) != 0))) {
        (void)close(executable_fd);
        return 64;
    }
    if (executable_fd != 3 && close(executable_fd) != 0) {
        return 64;
    }
    (void)close(0);
    (void)close(1);
    (void)close(2);
    if (runtime_v3 &&
        (close(v3_map.report_fd) != 0 || !v3_read_exact_go(v3_map.ack_fd) ||
         close(v3_map.ack_fd) != 0 || close(v3_map.readback_fd) != 0 ||
         close(v3_map.verifier_procs_fd) != 0 ||
         close(v3_map.verifier_events_fd) != 0 ||
         close(v3_map.verifier_kill_fd) != 0 ||
         attach_v3_worker_authorities() != 0))
        return 64;
    if (!close_worker_descriptors(status_descriptor, acknowledgement_descriptor,
                                  -1, -1)) {
        return 64;
    }
    if (!(runtime_v3 ? enforce_seccomp_v3(false) == 0 : enforce_seccomp(runtime_v2))) {
        return 64;
    }
    if (status_descriptor >= 0) {
        readiness_length = snprintf(readiness, sizeof(readiness),
                                     WORKER_READY_PREFIX "%ld" WORKER_READY_SUFFIX,
                                    controller_visible_pid);
        if (readiness_length < 0 || (size_t)readiness_length >= sizeof(readiness) ||
            write_all(status_descriptor, readiness, (size_t)readiness_length) != 0 ||
            close(status_descriptor) != 0) {
            return 64;
        }
    }
    if (acknowledgement_descriptor >= 0) {
        char acknowledgement;

        if (read(acknowledgement_descriptor, &acknowledgement, 1U) != 1 ||
            acknowledgement != '1' || close(acknowledgement_descriptor) != 0) {
            return 64;
        }
    }
    if (runtime_v3) {
        (void)close(v3_map.map_fd);
        (void)close(v3_map.report_fd);
        for (size_t index = 0U; index < v3_map.count; index++)
            (void)close(v3_map.rows[index].fd);
        (void)close(v3_map.loader_fd);
    }
    /* AT_EMPTY_PATH binds exec to the same object Landlock admitted. */
    if (runtime_v2) {
        (void)syscall(SYS_execveat, 3, "", argv + executable_index, environment,
                      AT_EMPTY_PATH);
        (void)close(3);
        return 64;
    }
    if (runtime_v3) {
        size_t count = 0U;
        v3_argv[count++] = (char *)"/ranex/runtime/loader/ld-linux-x86-64.so.2";
        v3_argv[count++] = (char *)"--inhibit-cache";
        v3_argv[count++] = (char *)"--glibc-hwcaps-mask";
        v3_argv[count++] = (char *)"";
        v3_argv[count++] = (char *)"--library-path";
        v3_argv[count++] = (char *)"/ranex/runtime/lib";
        v3_argv[count++] = (char *)"--argv0";
        v3_argv[count++] = argv[executable_index];
        for (int index = executable_index; index < argc && count + 1U < sizeof(v3_argv) / sizeof(v3_argv[0]); index++)
            v3_argv[count++] = argv[index];
        v3_argv[count] = NULL;
        (void)v3_worker_exec("3", v3_argv, environment);
    } else {
        (void)syscall(SYS_execveat, 3, "", argv + argument_offset + 4, environment,
                      AT_EMPTY_PATH);
        (void)close(3);
        return 64;
    }
    (void)close(3);
    return 64;
}

int main(int argc, char **argv) {
    if (argc == 1) {
        return stage_one();
    }
    if (argc >= 2 && strcmp(argv[1], STAGE_TWO) == 0) {
        return stage_two(argc, argv);
    }
    if (argc >= 2 && strcmp(argv[1], WORKER_EXEC) == 0) {
        int result = worker_exec(argc, argv);
        if (result != 0 && (v3_report_descriptor >= 0 ||
                            (argc >= 3 && strstr(argv[2], WORKER_RUNTIME_V3) != NULL))) {
            char reason[160];
            int saved_errno = errno;
            (void)snprintf(reason, sizeof(reason), "runtime v3 refused: %s",
                           strerror(saved_errno));
            v3_diagnostic(reason);
        }
        return result;
    }
    return protocol_refusal();
}
